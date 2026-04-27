import mysql.connector
from contextlib import closing
from config import DATABASE_CONFIG
import time

CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    Address TEXT,
    phonenumber VARCHAR(255),
    password VARCHAR(255)
)
"""


def get_connection():
    return mysql.connector.connect(**DATABASE_CONFIG)


def initialize_database():
    max_retries = 10
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            with closing(get_connection()) as db:
                with closing(db.cursor()) as cursor:
                    cursor.execute(CREATE_TABLE_QUERY)
                    db.commit()
            return  # Success
        except mysql.connector.Error as e:
            if attempt < max_retries - 1:
                print(f"Database connection attempt {attempt + 1}/{max_retries} failed. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to database after {max_retries} attempts.")
                raise


def create_user(name, email, address, phonenumber, hashed_password):
    with closing(get_connection()) as db:
        with closing(db.cursor()) as cursor:
            insert_query = """
            INSERT INTO user (name, email, Address, phonenumber, password)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (name, email, address, phonenumber, hashed_password))
            db.commit()
            user_id = cursor.lastrowid

    users = get_user_by_id(user_id)
    return users[0] if users else None


def get_user_by_id(user_id):
    with closing(get_connection()) as db:
        with closing(db.cursor()) as cursor:
            select_query = "SELECT id, name, email, Address, phonenumber FROM user WHERE id = %s"
            cursor.execute(select_query, (user_id,))
            rows = cursor.fetchall()

    return [row_to_dict(row) for row in rows]


def delete_user_by_id(user_id):
    with closing(get_connection()) as db:
        with closing(db.cursor()) as cursor:
            delete_query = "DELETE FROM user WHERE id = %s"
            cursor.execute(delete_query, (user_id,))
            db.commit()
            
            # Check if any users remain
            cursor.execute("SELECT COUNT(*) FROM user")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # If no users left, reset AUTO_INCREMENT to 1
                cursor.execute("ALTER TABLE user AUTO_INCREMENT = 1")
            else:
                # Otherwise, set it to max(id) + 1
                cursor.execute("SELECT MAX(id) FROM user")
                max_id = cursor.fetchone()[0]
                if max_id:
                    cursor.execute(f"ALTER TABLE user AUTO_INCREMENT = {max_id + 1}")
            
            db.commit()


def row_to_dict(row):
    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "address": row[3],
        "phonenumber": row[4],
    }
