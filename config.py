import os

if os.getenv("ENV") == "test":
    DATABASE_CONFIG = {
        "database": ":memory:"
    }
else:
    DATABASE_CONFIG = {
        "host": "mysql",
        "user": "root",
        "password": "root",
        "database": "testdb"
    }
