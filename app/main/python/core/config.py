from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Any
from pydantic import BeforeValidator
from typing_extensions import Annotated

def parse_cors(v: Any) -> List[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///test.db"
    NOSQL_DATABASE_URL: str = "mongodb://localhost:27017/chesspunk"
    DB_ENGINE: str = "SQL"
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    CORS_ORIGINS: Annotated[list[str], BeforeValidator(parse_cors)] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

settings = Settings()
