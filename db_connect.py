from sqlalchemy import create_engine
import os

def get_db_credentials():
    # Use the absolute path for the credentials directory
    dbcreds_path = os.path.join('../.cred', 'dbcreds')
    if os.path.exists(dbcreds_path):
        with open(dbcreds_path, 'r') as file:
            db_creds = file.read().strip().split(',')
            if len(db_creds) != 4:
                raise ValueError("DB credentials file 'dbcreds' is not formatted correctly.")
            return db_creds
    else:
        raise FileNotFoundError("DB credentials file 'dbcreds' not found.")

def create_db_engine():
    db_host, db_user, db_password, db_name = get_db_credentials()
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}"
    engine = create_engine(connection_string, echo=True)
    return engine