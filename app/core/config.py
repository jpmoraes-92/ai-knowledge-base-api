from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    mongo_uri: str
    database_name: str
    openai_api_key: str
    embedding_model: str
    llm_model: str
    top_k: int = 3

    # Sintaxe atualizada para evitar o DeprecationWarning
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()