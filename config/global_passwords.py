# Create a "passwords.py" file, put it only on your production server right next
# to this passwords.py.example file.  Add to it the passwords and usernames detailed
# in this file.

# Store your passwords.  Do so somewhere that is secure, and in a way that will
# be accessible to you in the future.

# THESE ARE NOT THE DATA ENCRYPTION KEYS, THOSE ARE NOT STORED HERE.

# Do not use the example keys provided on any production environment.

# We STRONGLY recommend using a cryptographically secure random number generator
# to generate your passwords; your passwords should not be easy to remember.

# These are the credentials used to access the MongoDB that contains website
# usernames and passwords.  If you are configuring your server see the comment
# at the end of this document.
MONGO_USERNAME = "beiwe"
MONGO_PASSWORD = "PhWY9uFaXScfU4uZeQXd"

# This is the secret key for the website, it is used in securing the website
# and config stored for each user.
# Do not use the example provided in this document
FLASK_SECRET_KEY = "abcdefghijklmnopqrstuvwxyz012345"

# These are your AWS (Amazon Web Services) access credentials.
# (Amazon provides you with these credentials, you do not generate them.)

aws_access_key_id = "aws_access_credential"
aws_secret_access_key = "aws_access_credential"


"""            Setting up MongoDB and mongolia

If you have set up a different default location for the conf, go edit that file,
otherwise cd to /etc, edit mongodb.conf using superuser privilages.
find the line #auth=true and remove the comment (the #)
run: sudo service mongod restart

in a python terminal:
import mongolia
mongolia.add_user( "beiwe", "PhWY9uFaXScfU4uZeQXd" )
mongolia.authenticate_connection( "beiwe", "PhWY9uFaXScfU4uZeQXd" )
exit()
"""