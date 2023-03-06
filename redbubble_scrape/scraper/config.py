from pydantic import BaseSettings
import os


path_to_dotenv = os.path.join(os.path.dirname(__file__), "..", ".env")


class Settings(BaseSettings):
    """
    Set the Environment Variables Automatically using Pydantic
    """
    PYTHON_RUNNING_IN_CONTAINER: bool = False
    USE_REMOTE_WEBDRIVER: bool = False

    class Config:
        env_file = path_to_dotenv
        env_file_encoding = 'utf-8'


SETTINGS = Settings()
