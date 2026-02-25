from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongo_uri: str
    database_name: str
    openai_api_key: str
    embedding_model: str
    llm_model: str
    top_k: int = 3

    class Config:
        env_file = ".env"

settings = Settings()