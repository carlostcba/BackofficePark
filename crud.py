from sqlalchemy.orm import Session, selectinload
from datetime import datetime, timedelta
from typing import Optional
import logging
import mercadopago

import models, schemas, security
from settings import settings

# --- Funciones de Refresco de Token ---

def refresh_seller_tokens(db: Session, seller: models.Seller) -> models.Seller:
    """
    Usa el refresh_token de un vendedor para obtener un nuevo access_token y 
    actualiza al vendedor en la base de datos.
    """
    sdk = mercadopago.SDK(settings.MP_SECRET_KEY)
    try:
        credentials = sdk.refresh_credentials(seller.mp_refresh_token)
        if not credentials or "response" not in credentials or "access_token" not in credentials["response"]:
            # Aquí se debería loguear el error. Si el refresh falla, es un problema serio.
            # Por ahora, simplemente devolvemos el vendedor sin cambios.
            return seller

        access_token = credentials["response"]["access_token"]
        refresh_token = credentials["response"]["refresh_token"]

        # Guardar los nuevos tokens
        return update_seller_mp_tokens(
            db=db,
            seller_id=seller.id,
            access_token=access_token,
            refresh_token=refresh_token
        )
    except Exception as e:
        # Loguear el error e
        return seller

# --- CRUD para Seller ---

def get_seller(db: Session, seller_id: int):
    return db.query(models.Seller).filter(models.Seller.id == seller_id).first()

def get_seller_by_email(db: Session, email: str):
    return db.query(models.Seller).options(selectinload(models.Seller.totems)).filter(models.Seller.email == email).first()

def get_sellers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Seller).offset(skip).limit(limit).all()

def create_seller(db: Session, seller: schemas.SellerCreate):
    hashed_password = security.get_password_hash(seller.password)
    db_seller = models.Seller(name=seller.name, email=seller.email, hashed_password=hashed_password)
    db.add(db_seller)
    db.commit()
    db.refresh(db_seller)
    return db_seller

def update_seller(db: Session, seller_id: int, seller_update: schemas.SellerUpdate):
    db_seller = db.query(models.Seller).filter(models.Seller.id == seller_id).first()
    if db_seller:
        update_data = seller_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_seller, key, value)
        db.add(db_seller)
        db.commit()
        db.refresh(db_seller)
    return db_seller

def update_seller_mp_tokens(db: Session, seller_id: int, access_token: str, refresh_token: str):
    db_seller = db.query(models.Seller).filter(models.Seller.id == seller_id).first()
    if db_seller:
        db_seller.mp_access_token = access_token
        db_seller.mp_refresh_token = refresh_token
        db_seller.mp_token_last_updated = datetime.utcnow()
        db.add(db_seller)
        db.commit()
        db.refresh(db_seller)
    return db_seller

def disconnect_seller_mp(db: Session, seller_id: int):
    db_seller = db.query(models.Seller).filter(models.Seller.id == seller_id).first()
    if db_seller:
        db_seller.mp_access_token = None
        db_seller.mp_refresh_token = None
        db_seller.mp_token_last_updated = None
        db.add(db_seller)
        db.commit()
        db.refresh(db_seller)
    return db_seller

def delete_seller(db: Session, seller_id: int):
    db_seller = db.query(models.Seller).filter(models.Seller.id == seller_id).first()
    if db_seller:
        db.delete(db_seller)
        db.commit()
    return db_seller

# --- CRUD para Totem ---

def get_totem(db: Session, totem_id: int):
    return db.query(models.Totem).filter(models.Totem.id == totem_id).first()

def get_totem_by_external_id(db: Session, external_pos_id: str):
    return db.query(models.Totem).filter(models.Totem.external_pos_id == external_pos_id).first()

def get_totems(db: Session, skip: int = 0, limit: int = 100, owner_id: int = None):
    query = db.query(models.Totem)
    if owner_id:
        query = query.filter(models.Totem.owner_id == owner_id)
    return query.offset(skip).limit(limit).all()

def create_totem(db: Session, totem: schemas.TotemCreate):
    db_totem = models.Totem(
        external_pos_id=totem.external_pos_id,
        location=totem.location,
        is_active=totem.is_active,
        owner_id=totem.owner_id
    )
    db.add(db_totem)
    db.commit()
    db.refresh(db_totem)
    return db_totem

def update_totem(db: Session, totem_id: int, totem_update: schemas.TotemUpdate):
    db_totem = db.query(models.Totem).filter(models.Totem.id == totem_id).first()
    if db_totem:
        update_data = totem_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_totem, key, value)
        db.add(db_totem)
        db.commit()
        db.refresh(db_totem)
    return db_totem

def delete_totem(db: Session, totem_id: int):
    db_totem = db.query(models.Totem).filter(models.Totem.id == totem_id).first()
    if db_totem:
        db.delete(db_totem)
        db.commit()
    return db_totem

def get_payments_by_seller(
    db: Session, 
    seller_id: int, 
    skip: int = 0, 
    limit: int = 20, 
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None
):
    """
    Obtiene los pagos de un vendedor específico, con filtros opcionales de fecha,
    ordenados por fecha descendente.
    """
    query = db.query(models.Payment).filter(models.Payment.seller_id == seller_id)
    if start_date:
        query = query.filter(models.Payment.payment_time >= start_date)
    if end_date:
        # Añadimos un día para que la fecha final sea inclusiva
        query = query.filter(models.Payment.payment_time < end_date + timedelta(days=1))
        
    return query\
        .order_by(models.Payment.payment_time.desc())\
        .offset(skip).limit(limit).all()

def create_parking_events(db: Session, events: list[schemas.ParkingEventCreate]):
    # Esta función podría ser más compleja, manejando duplicados, etc.
    # Por ahora, simplemente los crea.
    for event_data in events:
        db_event = models.ParkingEvent(**event_data.model_dump())
        db.add(db_event)
    db.commit()
    return

def process_payment_notification(db: Session, payment_id: str):
    """
    Obtiene los detalles de un pago de MP y lo guarda en la BD del backoffice.
    """
    try:
        # Usamos el token del marketplace para poder ver todos los pagos
        sdk = mercadopago.SDK(settings.MP_SECRET_KEY) # Asumiendo que el secret es el access token del marketplace
        payment_info = sdk.payment().get(payment_id)

        if payment_info["status"] != 200:
            logging.error(f"No se pudo obtener el detalle del pago {payment_id} desde Mercado Pago.")
            return

        payment = payment_info["response"]
        
        # Parsear la referencia externa para obtener ticket y pos_id
        external_reference = payment.get("external_reference", "")
        parts = external_reference.split('-')
        ticket_code = parts[0] if parts else None
        external_pos_id = parts[1] if len(parts) > 1 else None

        # Encontrar al vendedor a través del tótem
        seller_id = None
        if external_pos_id:
            totem = get_totem_by_external_id(db, external_pos_id)
            if totem:
                seller_id = totem.owner_id

        db_payment = models.Payment(
            mp_payment_id=str(payment["id"]),
            ticket_code=ticket_code,
            external_pos_id=external_pos_id,
            amount=payment["transaction_amount"],
            status=payment["status"],
            payment_time=datetime.fromisoformat(payment["date_approved"]),
            seller_id=seller_id
        )
        db.add(db_payment)
        db.commit()
        logging.info(f"Pago {payment_id} procesado y guardado en la base de datos del backoffice.")

    except Exception as e:
        logging.error(f"Error procesando la notificación de pago {payment_id}: {e}")
        db.rollback()
