from pydantic import BaseSettings
import os


path_to_dotenv = os.path.join(os.path.dirname(__file__), "..", ".env")


class Settings(BaseSettings):
    """
    Set the Environment Variables Automatically using Pydantic
    """
    python_running_in_container: bool = False
    use_remote_webdriver: bool = False


SETTINGS = Settings()
