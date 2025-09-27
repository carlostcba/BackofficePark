from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets
from pathlib import Path

# Construye una ruta absoluta al directorio del proyecto para que .env se encuentre siempre
BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    # Para desarrollo, podemos usar una base de datos SQLite en archivo.
    # En producción, esto cambiará a la URL de tu base de datos MySQL.
    DATABASE_URL: str = "sqlite:///./test.db"

    # Clave secreta para firmar los JWT. ¡Debe ser secreta!
    # Puedes generar una nueva con: openssl rand -hex 32
    SECRET_KEY: str = secrets.token_hex(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Variables para MercadoPago
    MP_APP_ID: str = ""
    MP_SECRET_KEY: str = ""
    MP_REDIRECT_URI: str = "https://127.0.0.1:8000/mercadopago/connect" # Default para desarrollo

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")


settings = Settings()
