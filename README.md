# Backoffice App - OemTotemPark

## Descripción

Esta es una aplicación web de backoffice basada en **FastAPI** que sirve como panel de control y API central para el sistema de estacionamiento OemTotemPark. Su función es doble:

1.  **Panel de Vendedor**: Ofrece una interfaz web simple para que los dueños de estacionamientos (Vendedores) puedan gestionar sus tótems y, fundamentalmente, conectar de forma segura su cuenta de Mercado Pago para recibir los cobros.
2.  **API para Tótems**: Provee una API segura y robusta para que los tótems físicos puedan obtener las credenciales necesarias para operar y registrar eventos.

La aplicación ha sido corregida para solucionar un error de sintaxis (`async async`) que impedía su inicio.

## Características Principales

-   **Gestión de Vendedores**: Sistema completo de registro y autenticación para vendedores usando JWT (JSON Web Tokens).
-   **Gestión de Tótems**: Endpoints para crear, ver, actualizar y eliminar tótems, siempre asociados a un vendedor.
-   **Integración Segura con Mercado Pago**:
    -   Flujo OAuth 2.0 completo para que los vendedores vinculen su cuenta de Mercado Pago sin compartir credenciales sensibles.
    -   Almacenamiento seguro de tokens de acceso y de refresco.
    -   Refresco automático de tokens de acceso para mantener la conexión activa.
-   **API Robusta para Tótems**:
    -   Autenticación segura mediante `X-API-Key`.
    -   Un endpoint dedicado para que el tótem solicite el `access_token` vigente de su vendedor, asegurando que siempre pueda cobrar.
-   **Recepción de Pagos**: Endpoint de Webhook (IPN) para recibir notificaciones de pago de Mercado Pago y procesarlas en segundo plano.
-   **Visualización de Datos**: Endpoints para que el vendedor autenticado pueda ver su información, sus tótems y su historial de pagos.
-   **Roles de Usuario**: Implementación de un rol de `admin` para futuras operaciones privilegiadas.
-   **Interfaz Web**: Vistas básicas generadas con plantillas Jinja2 para el login y un dashboard de gestión.

## Stack Tecnológico

-   **Backend**: FastAPI
-   **Servidor ASGI**: Uvicorn
-   **Base de Datos**: SQLAlchemy ORM (configurable para SQLite, MySQL, PostgreSQL, etc.)
-   **Validación de Datos**: Pydantic
-   **Autenticación**: Passlib (para hashing de contraseñas), python-jose (para JWT).
-   **Configuración**: Pydantic-Settings para gestionar variables de entorno.
-   **Frontend**: Jinja2 para renderizado de plantillas HTML.

## Estructura del Proyecto

```
.
├─── main.py         # Fichero principal de la API, define los endpoints y la lógica de la aplicación.
├─── crud.py         # Contiene las funciones para interactuar con la BD (Crear, Leer, Actualizar, Borrar).
├─── models.py       # Define los modelos de la base de datos usando SQLAlchemy.
├─── schemas.py      # Define los esquemas de datos de Pydantic para validación y serialización.
├─── security.py     # Lógica de autenticación, hashing de contraseñas y gestión de tokens JWT.
├─── settings.py     # Carga y gestiona la configuración desde variables de entorno.
├─── database.py     # Configura la conexión a la base de datos y las sesiones.
├─── requirements.txt# Lista de dependencias de Python.
├─── static/         # Ficheros estáticos (CSS, JS, imágenes).
└─── templates/      # Plantillas HTML (Jinja2).
```

## Configuración y Puesta en Marcha

1.  **Clonar el Repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd OemTotemPark/backoffice_app
    ```

2.  **Crear y Activar un Entorno Virtual:**
    ```bash
    python -m venv venv
    # En Windows:
    venv\Scripts\activate
    # En macOS/Linux:
    source venv/bin/activate
    ```

3.  **Instalar Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Variables de Entorno:**
    Cree un archivo llamado `.env` en la raíz del directorio `backoffice_app`. Este archivo contendrá los secretos y la configuración de la aplicación.

    ```env
    # --- Base de Datos ---
    # Usar esta línea para una base de datos SQLite local para pruebas
    DATABASE_URL="sqlite:///./test.db"
    # Ejemplo para MySQL (requiere instalar 'mysqlclient' o 'PyMySQL'):
    # DATABASE_URL="mysql+pymysql://user:password@host:port/database"

    # --- Seguridad JWT ---
    # Generar una clave segura con: openssl rand -hex 32
    SECRET_KEY="<UNA_CLAVE_SECRETA_MUY_LARGA_Y_ALEATORIA>"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=60

    # --- Mercado Pago ---
    # Credenciales de TU aplicación en Mercado Pago
    MP_APP_ID="<TU_APP_ID_DE_MERCADO_PAGO>"
    MP_SECRET_KEY="<TU_SECRET_KEY_DE_MERCADO_PAGO>"
    # URL a la que MP redirigirá al usuario tras el OAuth. Debe coincidir con la configurada en tu app de MP.
    MP_REDIRECT_URI="http://127.0.0.1:8000/mercadopago/connect"

    # --- API Key para Tótems ---
    # Clave que los tótems usarán para autenticarse. Generar con: openssl rand -hex 32
    TOTEM_API_KEY="<UNA_CLAVE_SECRETA_PARA_LA_API_DE_TOTEMS>"
    ```

5.  **Iniciar la Aplicación:**
    El error de sintaxis ha sido corregido, por lo que la aplicación debería iniciar correctamente.
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
    -   `--reload`: El servidor se reiniciará automáticamente al detectar cambios en el código.
    -   La aplicación estará disponible en `http://127.0.0.1:8000`.
    -   La documentación interactiva de la API (Swagger UI) estará en `http://127.0.0.1:8000/docs`.