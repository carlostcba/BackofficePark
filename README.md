# Backoffice App - OemTotemPark

## Descripción

Esta es una aplicación web de backoffice basada en **FastAPI** que sirve como panel de control y gestión central para el sistema de estacionamiento OemTotemPark. Permite a los administradores y vendedores gestionar sus tótems, credenciales de Mercado Pago y visualizar el historial de pagos.

## Características Principales

- **Gestión de Usuarios:** Sistema de autenticación basado en JWT con roles (vendedor, administrador).
- **Dashboard Intuitivo:** Una interfaz de usuario web para:
    - Visualizar la información del vendedor y el estado de su conexión con Mercado Pago.
    - Conectar y desconectar la cuenta de Mercado Pago de forma segura (flujo OAuth).
    - Visualizar y gestionar de forma segura los tokens de API de Mercado Pago.
- **Gestión de Tótems:** Permite a los vendedores añadir, editar y ver el estado de sus tótems de pago.
- **API Segura para Tótems:** Provee endpoints seguros para que los dispositivos tótem recuperen las credenciales de Mercado Pago necesarias para operar.
- **Historial de Pagos:** Muestra un registro de todos los pagos procesados a través de los tótems del vendedor, con paginación y filtros por fecha.

## Stack Tecnológico

- **Backend:** FastAPI
- **Base de Datos:** SQLAlchemy (compatible con SQLite, PostgreSQL, etc.)
- **Validación de Datos:** Pydantic
- **Autenticación:** JWT (python-jose), Passlib
- **Frontend:** Jinja2 para el renderizado de plantillas HTML, con CSS y JavaScript vainilla.
- **Servidor ASGI:** Uvicorn

## Configuración y Puesta en Marcha

1.  **Clonar el Repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd OemTotemPark/backoffice_app
    ```

2.  **Crear un Entorno Virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instalar Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Variables de Entorno:**
    Cree un archivo `.env` en el directorio `backoffice_app` basándose en el siguiente ejemplo:
    ```env
    # URL de la base de datos. Para SQLite:
    DATABASE_URL="sqlite:///./test.db"
    # Clave secreta para firmar los tokens JWT (generar una clave segura)
    SECRET_KEY="tu_super_secreta_y_larga_clave_aqui"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    # Credenciales de la aplicación de Mercado Pago (para el flujo OAuth)
    MP_APP_ID="TU_APP_ID_DE_MP"
    MP_APP_SECRET="TU_APP_SECRET_DE_MP"
    # URL base donde esta aplicación está alojada (para los redirects de OAuth)
    BASE_URL="http://localhost:8000"
    ```

5.  **Iniciar la Aplicación:**
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
    La aplicación estará disponible en `http://localhost:8000`.

## Estructura del Proyecto

```
.
├─── crud.py         # Lógica de acceso a datos (CRUD)
├─── database.py     # Configuración de la conexión a la BD y sesión
├─── main.py         # Fichero principal de la API, define los endpoints
├─── models.py       # Modelos de la base de datos (SQLAlchemy)
├─── schemas.py      # Esquemas de datos (Pydantic) para la API
├─── security.py     # Lógica de autenticación y seguridad
├─── settings.py     # Carga de la configuración y variables de entorno
├─── requirements.txt# Dependencias de Python
├─── static/         # Ficheros estáticos (CSS, JS, imágenes)
└─── templates/      # Plantillas HTML (Jinja2)
```
