from bson.objectid import ObjectId
from csv import writer
from flask import abort, Blueprint, make_response, redirect, request, Response
from flask.templating import render_template
from re import sub

from config.secure_settings import IS_STAGING
from libs.admin_authentication import authenticate_admin_study_access,\
    authenticate_system_admin, authenticate_admin_login, admin_is_system_admin,\
    get_admins_allowed_studies
from libs.s3 import s3_upload, create_client_key_pair
from libs.streaming_bytes_io import StreamingBytesIO
from libs.security import check_password_requirements

# Mongolia models
from db.user_models import Admin
from db.study_models import Study, Studies

# Django models
from study.models import Participant, Researcher, Study as DStudy

admin_api = Blueprint('admin_api', __name__)

"""######################### Study Administration ###########################"""


@admin_api.route('/add_admin_to_study', methods=['POST'])
@authenticate_system_admin
def add_admin_to_study():
    researcher_id = request.form.get('researcher_id')
    study_id = request.form.get('study_id')
    Researcher.objects.get(pk=researcher_id).studies.add(study_id)
    return '200'


@admin_api.route('/remove_admin_from_study', methods=['POST'])
@authenticate_system_admin
def remove_admin_from_study():
    researcher_id = request.form.get('admin_id')
    study_id = request.form.get('study_id')
    Researcher.objects.get(pk=researcher_id).studies.remove(study_id)
    return '200'


@admin_api.route('/delete_researcher/<string:admin_id>', methods=['GET','POST'])
@authenticate_system_admin
def delete_researcher(admin_id):
    admin = Admin(admin_id)
    if not admin:
        return abort(404)
    for study in Studies():
        study.remove_admin(admin_id)
    admin.remove()
    return redirect('/manage_researchers')


@admin_api.route('/set_researcher_password', methods=['POST'])
@authenticate_system_admin
def set_researcher_password():
    admin = Admin(request.form.get('admin_id'))
    new_password = request.form.get('password')
    if not check_password_requirements(new_password, flash_message=True):
        return redirect('/edit_researcher/' + admin._id)
    admin.set_password(new_password)
    return redirect('/edit_researcher/' + admin._id)


@admin_api.route('/rename_study/<string:study_id>', methods=['POST'])
@authenticate_system_admin
def rename_study(study_id=None):
    study = DStudy.objects.get(pk=study_id)
    new_study_name = request.form.get('new_study_name')
    study.name = new_study_name
    study.save()
    return redirect('/edit_study/{:d}'.format(study.pk))


"""########################## User Administration ###########################"""


@admin_api.route('/reset_patient_password/<string:study_id>', methods=["POST"])
@authenticate_admin_study_access
def reset_user_password(study_id=None):
    """ Takes a patient ID and resets its password. Returns the new random password."""
    patient_id = request.values["patient_id"]
    participant_set = Participant.objects.filter(patient_id=patient_id)
    if participant_set.exists() and participant_set.values_list('study', flat=True).get() == int(study_id):
        participant = participant_set.get()
        new_password = participant.reset_password()
        return make_response(new_password, 201)
    else:
        return make_response("that patient id does not exist", 404)


@admin_api.route('/reset_device/<string:study_id>', methods=["POST"])
@authenticate_admin_study_access
def reset_device(study_id=None):
    """
    Resets a patient's device.  The patient will not be able to connect until expect to
    register a new device.
    """

    # AJK TODO look into making this an HTML hidden input and fiddling with authenticate_admin_study_access
    patient_id = request.values["patient_id"]
    participant_set = Participant.objects.filter(patient_id=patient_id)
    if participant_set.exists() and participant_set.values_list('study', flat=True).get() == int(study_id):
        participant = participant_set.get()
        participant.clear_device()
        return make_response("device was reset; password is untouched.", 201)
    else:
        return make_response("that patient id does not exist", 404)


@admin_api.route('/create_new_patient/<string:study_id>', methods=["POST"])
@authenticate_admin_study_access
def create_new_patient(study_id=None):
    """
    Creates a new user, generates a password and keys, pushes data to s3 and user database, adds
    user to the study they are supposed to be attached to and returns a string containing
    password and patient id.
    """

    patient_id, password = Participant.create_with_password(study_id=study_id)
    # Create an empty file on S3 indicating that this user exists
    study_object_id = DStudy.objects.filter(pk=study_id).values_list('object_id', flat=True).get()
    s3_upload(patient_id, "", study_object_id)
    create_client_key_pair(patient_id, study_object_id)
    response_string = "patient_id: " + patient_id + "\npassword: " + password
    return make_response(response_string, 201)


@admin_api.route('/create_many_patients/<string:study_id>', methods=["POST"])
@authenticate_admin_study_access
def create_many_patients(study_id=None):
    """ Creates a number of new users at once for a study.  Generates a password and keys for
    each one, pushes data to S3 and the user database, adds users to the study they're supposed
    to be attached to, and returns a CSV file for download with a mapping of Patient IDs and
    passwords. """
    number_of_new_patients = int(request.form.get('number_of_new_patients'))
    desired_filename = request.form.get('desired_filename')
    filename_spaces_to_underscores = sub(r'[\ =]', '_', desired_filename)
    filename = sub(r'[^a-zA-Z0-9_\.=]', '', filename_spaces_to_underscores)
    if not filename.endswith('.csv'):
        filename += ".csv"
    return Response(csv_generator(study_id, number_of_new_patients),
                    mimetype="csv",
                    headers={'Content-Disposition': 'attachment; filename="%s"' % filename})


def csv_generator(study_id, number_of_new_patients):
    si = StreamingBytesIO()
    filewriter = writer(si)
    filewriter.writerow(['Patient ID', "Registration password"])
    study_object_id = DStudy.objects.filter(pk=study_id).values_list('object_id', flat=True).get()
    for _ in xrange(number_of_new_patients):
        patient_id, password = Participant.create_with_password(study_id=study_id)
        # Creates an empty file on s3 indicating that this user exists
        s3_upload(patient_id, "", study_object_id)
        create_client_key_pair(patient_id, study_object_id)
        filewriter.writerow([patient_id, password])
        yield si.getvalue()
        si.empty()


"""##### Methods responsible for distributing APK file of Android app. #####"""

@admin_api.route("/downloads")
@authenticate_admin_login
def download_page():
    return render_template("download_landing_page.html",
                           system_admin=admin_is_system_admin(),
                           allowed_studies=get_admins_allowed_studies())


@admin_api.route("/download")
def download_current():
    return redirect("https://s3.amazonaws.com/beiwe-app-backups/release/Beiwe.apk")

@admin_api.route("/download_debug")
@authenticate_admin_login
def download_current_debug():
    return redirect("https://s3.amazonaws.com/beiwe-app-backups/release/Beiwe-debug.apk")

@admin_api.route("/download_beta")
@authenticate_admin_login
def download_beta():
    return redirect("https://s3.amazonaws.com/beiwe-app-backups/release/Beiwe.apk")

@admin_api.route("/download_beta_debug")
@authenticate_admin_login
def download_beta_debug():
    return redirect("https://s3.amazonaws.com/beiwe-app-backups/debug/Beiwe-debug.apk")

@admin_api.route("/privacy_policy")
def download_privacy_policy():
    return redirect("https://s3.amazonaws.com/beiwe-app-backups/Beiwe+Data+Privacy+and+Security.pdf")

"""########################## Debugging Code ###########################"""

if IS_STAGING:
    @admin_api.route("/is_staging")
    def is_staging():
        return "yes"
