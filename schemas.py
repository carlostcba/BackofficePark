from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# --- Schemas de Autenticación ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Schemas para Seller ---

# Schema base con los campos comunes
class SellerBase(BaseModel):
    name: str
    email: EmailStr

# Schema para la creación de un Vendedor (lo que la API espera en un POST)
class SellerCreate(SellerBase):
    password: str

# Schema para la actualización de un Vendedor (todos los campos son opcionales)
class SellerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

# Forward declaration para evitar problemas de referencia circular
class Totem(BaseModel):
    id: int
    external_pos_id: str
    location: Optional[str] = None
    is_active: bool
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schema para leer/devolver un Vendedor (lo que la API devuelve)
# Nótese que no incluimos la contraseña por seguridad.
class Seller(SellerBase):
    id: int
    mp_access_token: Optional[str] = None # Para verificar el estado de conexión en el frontend
    created_at: datetime
    updated_at: datetime
    totems: List[Totem] = [] # Lista de tótems asociados

    class Config:
        from_attributes = True # Permite que el schema se cree desde un modelo de BD

# --- Schemas para Totem ---

class TotemBase(BaseModel):
    external_pos_id: str
    location: Optional[str] = None
    is_active: Optional[bool] = True
    owner_id: int

class TotemCreate(TotemBase):
    pass

class TotemUpdate(BaseModel):
    external_pos_id: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
    owner_id: Optional[int] = None

# El schema Totem ya está definido arriba para la forward declaration
