from pydantic_settings import BaseSettings,SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL:str
    JWT_SECRET:str
    JWT_ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int = 15
    model_config=SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

Config=Settings()