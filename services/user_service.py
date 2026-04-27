import bcrypt
from repositories.user_repository import initialize_database, create_user as repo_create_user, get_user_by_id, delete_user_by_id


def initialize_app_database():
    initialize_database()


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_user(name, email, address, phonenumber, password):
    hashed_password = hash_password(password)
    return repo_create_user(name, email, address, phonenumber, hashed_password)


def fetch_user_by_id(user_id):
    return get_user_by_id(user_id)


def remove_user_by_id(user_id):
    delete_user_by_id(user_id)
