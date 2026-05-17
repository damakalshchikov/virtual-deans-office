import os

SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    "postgresql://mad:22164251994Md@localhost:5432/virtual_dekanat"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads", "task_files")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
