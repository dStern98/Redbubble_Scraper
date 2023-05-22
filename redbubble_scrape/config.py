from pydantic import BaseSettings
import os
from pathlib import Path

path_to_dotenv = Path(os.path.dirname(__file__)) / ".." / ".env"


class Settings(BaseSettings):
    """
    Set the Environment Variables Automatically using Pydantic
    """
    PYTHON_RUNNING_IN_CONTAINER: bool = False
    USE_REMOTE_WEBDRIVER: bool = False
    MAX_ITEMS_PER_SCRAPE: int = 20
    BATCH_SIZE: int = 5
    DEBUG_MODE: bool = False

    class Config:
        env_file = path_to_dotenv
        env_file_encoding = 'utf-8'


SETTINGS = Settings()
