# FILE: config.py

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Manages application settings using Pydantic.
    Loads environment variables and validates them.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')
    CHROMA_DB_PATH: str = "chroma_db"

# Create a single, globally accessible instance of the settings
settings = Settings()