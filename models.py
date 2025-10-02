from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship

from database import Base

class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, server_default="seller") # 'seller' o 'admin'
    
    # Credenciales de Mercado Pago
    mp_access_token = Column(String(255), nullable=True)
    mp_refresh_token = Column(String(255), nullable=True)
    mp_token_last_updated = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relación con Tótems
    totems = relationship("Totem", back_populates="owner")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    mp_payment_id = Column(String(50), unique=True, index=True, nullable=False)
    ticket_code = Column(String(20), index=True, nullable=True)
    external_pos_id = Column(String(50), index=True, nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)
    payment_time = Column(DateTime, nullable=False)
    
    seller_id = Column(Integer, ForeignKey("sellers.id"))

    created_at = Column(DateTime, server_default=func.now())

class ParkingEvent(Base):
    __tablename__ = "parking_events"

    id = Column(Integer, primary_key=True, index=True)
    ticket_code = Column(String(20), nullable=False, index=True)
    device_id = Column(Integer, nullable=True)
    event_type = Column(String(10), nullable=False, index=True)
    event_time = Column(DateTime, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    sent_to_backoffice_at = Column(DateTime, nullable=True)


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
