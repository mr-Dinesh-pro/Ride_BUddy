import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Resolve absolute path to .env (located in parent of app/ folder, i.e., backend/)
current_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.abspath(os.path.join(current_dir, "..", ".env"))
load_dotenv(dotenv_path)

class Settings(BaseSettings):
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    class Config:
        env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        env_file_encoding = "utf-8"
        # Allow extra environment variables without throwing errors
        extra = "ignore"

# Instantiate settings
try:
    settings = Settings()
except Exception as e:
    # Provide a user-friendly error if environment variables are completely missing
    print(f"WARNING: Environment configuration error: {e}")
    print("Falling back to environment variable overrides or default values for development.")
    # Fallback to defaults or dummy variables for building/testing
    class DevSettings:
        NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
        NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")
    settings = DevSettings()
