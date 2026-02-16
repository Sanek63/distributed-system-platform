from pydantic_settings import BaseSettings


class Config(BaseSettings):
    APP_NAME: str
    SERVICE_B_URL: str
    OPENTELEMETRY_ENDRPOIND: str


config: Config = Config()
