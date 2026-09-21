from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # Telegram Bot
    telegram_bot_token: str

    # Token.club API
    tokenclub_api_key: str

    # Database
    database_url: str
    db_password: str

    # Application
    debug: bool = False
    log_level: str = "INFO"


settings = Settings()
