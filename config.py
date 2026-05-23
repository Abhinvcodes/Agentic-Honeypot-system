from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Giving them an empty string default ensures Pylance knows they are optional during manual calls,
    # but Pydantic will still strictly overwrite them using your .env values at runtime!
    AI_BASE_URL: str = Field(default="")
    AI_API_KEY: str = Field(default="")
    AI_MODEL_NAME: str = Field(default="")

    API_SECRET_KEY: str = Field(default="")

    # Automatically load from the local .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Instantiated as a singleton cleanly. Pylance will be happy now!
settings = Settings()