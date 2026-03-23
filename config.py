from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    whisper_model: str = "base"
    output_dir: str = "./output"
    max_short_duration: int = 60
    min_short_duration: int = 30
    web_host: str = "127.0.0.1"
    web_port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
