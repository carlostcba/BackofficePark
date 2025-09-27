from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import schemas, crud
from .database import SessionLocal
from .settings import settings

# --- Configuración de Seguridad ---

# Contexto para el hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de autenticación OAuth2 para Vendedores (Dashboard)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Esquema de autenticación por API Key para Tótems
api_key_header_scheme = APIKeyHeader(name="X-API-Key")

# --- Funciones de Contraseña ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que una contraseña en texto plano coincida con un hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña."""
    return pwd_context.hash(password)

# --- Funciones de Token JWT ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un nuevo token de acceso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Por defecto, el token expira en 15 minutos
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# --- Dependencias de Seguridad ---

async def get_current_user(token: str = Depends(oauth2_scheme)) -> schemas.Seller:
    """
    Dependencia para obtener el VENDEDOR actual a partir de un token JWT.
    Se usa para proteger los endpoints del dashboard.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    db = SessionLocal()
    try:
        user = crud.get_seller_by_email(db, email=token_data.email)
        if user is None:
            raise credentials_exception
        return user
    finally:
        db.close()

def validate_totem_api_key(api_key: str = Security(api_key_header_scheme)):
    """
    Dependencia para validar la API Key enviada por un Tótem.
    """
    if api_key != settings.TOTEM_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return True
