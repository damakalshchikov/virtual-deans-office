import os

SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    "postgresql://mad:22164251994Md@localhost:5432/virtual_dekanat"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
