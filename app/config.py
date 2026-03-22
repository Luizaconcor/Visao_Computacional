import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    DATABASE_PATH = os.path.abspath(os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "database", "evento.db")))
    UPLOAD_FOLDER = os.path.abspath(os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads", "fotos")))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5242880))
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
