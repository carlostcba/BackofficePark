from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from database import Base

class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Credenciales de Mercado Pago
    mp_access_token = Column(String(255), nullable=True)
    mp_refresh_token = Column(String(255), nullable=True)
    mp_token_last_updated = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relación con Totems
    totems = relationship("Totem", back_populates="owner")


class Totem(Base):
    __tablename__ = "totems"

    id = Column(Integer, primary_key=True, index=True)
    external_pos_id = Column(String(50), unique=True, index=True, nullable=False) # Ej: QR_CAJA_01
    location = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    # Clave foránea para el vendedor
    owner_id = Column(Integer, ForeignKey("sellers.id"))
    owner = relationship("Seller", back_populates="totems")

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
