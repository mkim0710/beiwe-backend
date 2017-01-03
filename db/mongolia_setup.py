import os
from mongolia import (connect_to_database, authenticate_connection, ID_KEY,
    REQUIRED, UPDATE, CHILD_TEMPLATE, DatabaseObject, DatabaseCollection,
    set_defaults_handling, set_type_checking, AlertLevel)

from mongolia.errors import MalformedObjectError, DatabaseConflictError
from config.secure_settings import MONGO_USERNAME, MONGO_PASSWORD, MONGO_PORT

# We are specifying the default database, see the mongolia documentation if you
# use a non-default configuration.

connect_to_database(port=MONGO_PORT)
authenticate_connection(MONGO_USERNAME, MONGO_PASSWORD)
set_defaults_handling(AlertLevel.error)
set_type_checking(AlertLevel.error)

