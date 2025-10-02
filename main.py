from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from datetime import timedelta, datetime, timezone
import mercadopago
import hmac
import hashlib
import logging
import os
import urllib.parse
import requests

import crud, models, schemas, security
from database import SessionLocal, engine
from settings import settings

# --- Constantes ---
# Un token de MP dura 6 horas (21600 segundos). Lo refrescamos proactivamente.
TOKEN_STALE_THRESHOLD_SECONDS = 19800  # 5.5 horas

# --- Setup de la App ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OEM Totem Park - Back Office API",
    version="0.1.0",
)

# Montar directorio estático
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# Configurar plantillas Jinja2
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


# --- Dependencias ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints de Mercado Pago OAuth ---

@app.get("/mercadopago/authorize-url", summary="Generar URL de conexión para un Vendedor")
def get_mercadopago_authorization_url(current_user: schemas.Seller = Depends(security.get_current_user)):
    """
    Genera la URL de autorización de Mercado Pago para que el vendedor 
    actualmente autenticado pueda vincular su cuenta.
    """
    base_url = "https://auth.mercadopago.com/authorization"
    params = {
        "client_id": settings.MP_APP_ID,
        "response_type": "code",
        "platform": "mp",
        "redirect_uri": settings.MP_REDIRECT_URI,
        "state": str(current_user.id) # Enviamos el ID del vendedor
    }
    auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return {"authorization_url": auth_url}

@app.get("/mercadopago/connect", summary="Callback de conexión de Mercado Pago")
def handle_mercadopago_connect(request: Request, db: Session = Depends(get_db)):
    """
    Este es el endpoint al que Mercado Pago redirige al vendedor después de la autorización.
    Captura el código, lo intercambia por tokens y los guarda.
    """
    code = request.query_params.get("code")
    seller_id = request.query_params.get("state")

    if not code or not seller_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'code' or 'state' parameter")

    # Intercambiar el código por credenciales
    TOKEN_URL = "https://api.mercadopago.com/oauth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = {
        "client_id": settings.MP_APP_ID,
        "client_secret": settings.MP_SECRET_KEY,
        "code": code,
        "redirect_uri": settings.MP_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()  # Lanza una excepción para errores HTTP (4xx o 5xx)
        token_info = response.json()

        access_token = token_info.get("access_token")
        refresh_token = token_info.get("refresh_token")

        if not access_token or not refresh_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to obtain access or refresh token from Mercado Pago")

        # Guardar los tokens en la base de datos
        crud.update_seller_mp_tokens(
            db=db,
            seller_id=int(seller_id),
            access_token=access_token,
            refresh_token=refresh_token
        )

    except requests.exceptions.HTTPError as http_err:
        # Loguear el error HTTP específico
        print(f"HTTP error during token exchange: {http_err}")
        print(f"Response content: {response.text}")
        raise HTTPException(status_code=response.status_code, detail=f"Mercado Pago token exchange failed: {response.text}")
    except Exception as e:
        # Loguear cualquier otro error
        print(f"An unexpected error occurred during token exchange: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {e}")

    # Redirigir a una página de éxito en el frontend (a futuro)
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/mercadopago/disconnect", summary="Desconectar la cuenta de Mercado Pago del Vendedor")
def disconnect_mercadopago(
    db: Session = Depends(get_db),
    current_user: schemas.Seller = Depends(security.get_current_user)
):
    """
    Desconecta la cuenta de Mercado Pago del vendedor actualmente autenticado,
    eliminando sus tokens de la base de datos.
    """
    crud.disconnect_seller_mp(db, seller_id=current_user.id)
    return {"status": "ok", "detail": "Mercado Pago account disconnected successfully."}


# --- Endpoints de Vistas (Frontend) ---

@app.get("/", summary="Página de Login")
def view_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", summary="Dashboard Principal")
def view_dashboard(request: Request):
    # Este es un placeholder. Lo implementaremos a continuación.
    # Por ahora, solo muestra una página simple.
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": {"name": "Usuario de Prueba"}})


# --- API para Tótems ---

@app.get("/api/v1/totems/token/{external_pos_id}", summary="Obtener token de MP para un Tótem")
def get_mp_token_for_totem(
    external_pos_id: str,
    db: Session = Depends(get_db),
    is_validated: bool = Depends(security.validate_totem_api_key)
):
    """
    Endpoint para que los tótems obtengan el access token de su vendedor.
    Refresca el token proactivamente si está a punto de expirar.
    Requiere autenticación por API Key (Header: X-API-Key).
    """
    try:
        db_totem = crud.get_totem_by_external_id(db, external_pos_id=external_pos_id)
        if not db_totem:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Totem not found")
        
        seller = db_totem.owner
        if not seller:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Totem has no owner")

        if not seller.mp_access_token or not seller.mp_refresh_token or not seller.mp_token_last_updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner has not connected or configured their Mercado Pago account")

        # Comprobar si el token está "vencido" y necesita refrescarse
        token_age = (datetime.now(timezone.utc) - seller.mp_token_last_updated.replace(tzinfo=timezone.utc)).total_seconds()
        
        refreshed_seller = seller
        if token_age > TOKEN_STALE_THRESHOLD_SECONDS:
            refreshed_seller = crud.refresh_seller_tokens(db, seller=seller)

        return {"mp_access_token": refreshed_seller.mp_access_token}
    except SQLAlchemyError as e:
        # Aquí podrías loguear el error `e` si lo necesitas
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error de conexión con la base de datos. El servicio no está disponible."
        )
    except Exception as e:
        # Captura cualquier otro error inesperado para evitar un crash
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocurrió un error interno inesperado: {e}"
        )

@app.get("/api/v1/payments/me", response_model=List[schemas.Payment], summary="Obtener mis pagos registrados")
def read_my_payments(
    skip: int = 0,
    limit: int = 20,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: schemas.Seller = Depends(security.get_current_user)
):
    """
    Devuelve una lista paginada de los pagos registrados para el vendedor
    actualmente autenticado. Permite filtrar por un rango de fechas.
    """
    payments = crud.get_payments_by_seller(
        db, 
        seller_id=current_user.id, 
        skip=skip, 
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )
    return payments

@app.post("/api/v1/events", summary="Registrar eventos de parking desde un Tótem")
def register_parking_events(
    events: List[schemas.ParkingEventCreate],
    db: Session = Depends(get_db),
    is_validated: bool = Depends(security.validate_totem_api_key)
):
    """
    Endpoint para que los tótems envíen lotes de eventos (entradas/salidas)
    para ser registrados en la base de datos central del backoffice.
    """
    try:
        crud.create_parking_events(db=db, events=events)
        return {"status": "ok", "detail": f"{len(events)} events registered."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register events: {e}"
        )

# --- Endpoints de Autenticación ---

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Endpoint de login. Recibe email (como username) y contraseña.
    Devuelve un token de acceso si las credenciales son correctas.
    """
    seller = crud.get_seller_by_email(db, email=form_data.username)
    if not seller or not security.verify_password(form_data.password, seller.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": seller.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- Endpoints para Sellers ---

@app.post("/sellers/", response_model=schemas.Seller, summary="Crear un nuevo Vendedor")
def create_seller(seller: schemas.SellerCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo vendedor (registro público).
    """
    db_seller = crud.get_seller_by_email(db, email=seller.email)
    if db_seller:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return crud.create_seller(db=db, seller=seller)

@app.get("/sellers/me", response_model=schemas.Seller, summary="Obtener datos del usuario actual")
def read_users_me(current_user: schemas.Seller = Depends(security.get_current_user)):
    """
    Devuelve la información del vendedor actualmente autenticado.
    """
    return current_user

@app.get("/sellers/", response_model=List[schemas.Seller], summary="Obtener lista de Vendedores (protegido)")
def read_sellers(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: schemas.Seller = Depends(security.get_current_user)
):
    """
    Devuelve una lista de vendedores. (Endpoint protegido)
    """
    sellers = crud.get_sellers(db, skip=skip, limit=limit)
    return sellers

# ... (los otros endpoints de seller como get, patch, delete se pueden proteger de manera similar)


# --- Endpoints para Totems (Protegidos) ---

@app.post("/totems/", response_model=schemas.Totem, summary="Crear un nuevo Totem (protegido)")
def create_totem(
    totem: schemas.TotemCreate, 
    db: Session = Depends(get_db), 
    current_user: schemas.Seller = Depends(security.get_current_user)
):
    """
    Crea un nuevo tótem. El tótem se asignará automáticamente al vendedor autenticado.
    """
    # Forzamos que el owner_id sea el del usuario autenticado
    if totem.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create totem for another seller")

    existing_totem = crud.get_totem_by_external_id(db, external_pos_id=totem.external_pos_id)
    if existing_totem:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Totem with this external_pos_id already exists")

    return crud.create_totem(db=db, totem=totem)


@app.get("/totems/", response_model=List[schemas.Totem], summary="Obtener lista de Totems")
def read_totems(skip: int = 0, limit: int = 100, owner_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Devuelve una lista de tótems. Si no se especifica owner_id, devuelve todos.
    (Este endpoint podría ser público o protegido dependiendo de la lógica de negocio)
    """
    totems = crud.get_totems(db, skip=skip, limit=limit, owner_id=owner_id)
    return totems

@app.get("/totems/{totem_id}", response_model=schemas.Totem, summary="Obtener un Totem por ID")
def read_totem(totem_id: int, db: Session = Depends(get_db)):
    db_totem = crud.get_totem(db, totem_id=totem_id)
    if db_totem is None:
        raise HTTPException(status_code=404, detail="Totem not found")
    return db_totem

@app.patch("/totems/{totem_id}", response_model=schemas.Totem, summary="Actualizar un Totem (protegido)")
def update_totem_endpoint(
    totem_id: int,
    totem_update: schemas.TotemUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.Seller = Depends(security.get_current_user),
):
    db_totem = crud.get_totem(db, totem_id=totem_id)
    if db_totem is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Totem not found")
    
    if db_totem.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this totem")

    return crud.update_totem(db=db, totem_id=totem_id, totem_update=totem_update)

@app.delete("/totems/{totem_id}", response_model=schemas.Totem, summary="Eliminar un Totem (protegido)")
def delete_totem_endpoint(
    totem_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.Seller = Depends(security.get_current_user),
):
    db_totem = crud.get_totem(db, totem_id=totem_id)
    if db_totem is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Totem not found")

    if db_totem.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this totem")

    return crud.delete_totem(db=db, totem_id=totem_id)

@app.delete("/sellers/{seller_id}", response_model=schemas.Seller, summary="Eliminar un Vendedor (protegido)")
def delete_seller_endpoint(
    seller_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.Seller = Depends(security.get_current_user),
):
    # En una app real, aquí habría una lógica de roles más compleja (ej. solo un admin puede borrar).
    # Por ahora, se requiere estar autenticado.
    db_seller = crud.get_seller(db, seller_id=seller_id)
    if db_seller is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
    
    # Opcional: impedir que un usuario se borre a sí mismo o solo permitir a admins.
    # if current_user.id == seller_id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete your own account.")

    return crud.delete_seller(db=db, seller_id=seller_id)


# --- Endpoints de Administración (Protegidos para rol 'admin') ---

@app.get("/api/v1/admin/sellers", response_model=List[schemas.Seller], summary="[Admin] Obtener todos los vendedores")
def admin_read_sellers(
    db: Session = Depends(get_db),
    admin_user: schemas.Seller = Depends(security.require_admin_user)
):
    """
    Devuelve una lista de todos los vendedores en el sistema.
    Solo accesible para usuarios con rol 'admin'.
    """
    return crud.get_sellers(db)

@app.post("/api/v1/admin/sellers", response_model=schemas.Seller, summary="[Admin] Crear un nuevo vendedor")
def admin_create_seller(
    seller: schemas.SellerCreate,
    db: Session = Depends(get_db),
    admin_user: schemas.Seller = Depends(security.require_admin_user)
):
    """
    Crea un nuevo vendedor (con rol 'seller' o 'admin').
    Solo accesible para usuarios con rol 'admin'.
    """
    db_seller = crud.get_seller_by_email(db, email=seller.email)
    if db_seller:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return crud.create_seller(db=db, seller=seller)

@app.patch("/api/v1/admin/sellers/{seller_id}", response_model=schemas.Seller, summary="[Admin] Actualizar un vendedor")
def admin_update_seller(
    seller_id: int,
    seller_update: schemas.SellerUpdate,
    db: Session = Depends(get_db),
    admin_user: schemas.Seller = Depends(security.require_admin_user)
):
    """
    Actualiza los datos de un vendedor específico.
    Solo accesible para usuarios con rol 'admin'.
    """
    return crud.update_seller(db=db, seller_id=seller_id, seller_update=seller_update)

@app.delete("/api/v1/admin/sellers/{seller_id}", response_model=schemas.Seller, summary="[Admin] Eliminar un vendedor")
def admin_delete_seller(
    seller_id: int,
    db: Session = Depends(get_db),
    admin_user: schemas.Seller = Depends(security.require_admin_user)
):
    """
    Elimina un vendedor del sistema.
    Solo accesible para usuarios con rol 'admin'.
    """
    return crud.delete_seller(db=db, seller_id=seller_id)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API del Back Office de OEM Totem Park"}