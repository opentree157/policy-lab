from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./policylab.db"
    artifact_storage_path: str = "./artifacts"
    app_env: str = "development"

    model_config = {"env_file": ".env"}


settings = Settings()
