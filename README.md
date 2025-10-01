# Backoffice para OEM Totem Park

## 1. Descripción General

Este proyecto es el **backend central** para el sistema de tótems de estacionamiento. Es una aplicación web construida con **FastAPI** que actúa como el cerebro del ecosistema, gestionando vendedores, tótems y la integración con Mercado Pago.

Su propósito es centralizar la lógica de negocio, la autenticación y la configuración, permitiendo que las aplicaciones de los tótems (`totem_app`) sean clientes ligeros y fáciles de gestionar.

---

## 2. Características Principales

- **API REST Moderna:** Construida con FastAPI, ofrece una API rápida, segura y con documentación automática (Swagger UI).
- **Gestión Multi-Vendedor:** Diseñada desde cero para soportar múltiples vendedores (estacionamientos), cada uno con sus propios tótems.
- **Sistema de Roles:** Incluye roles de `admin` y `seller`, permitiendo una gestión jerárquica de la plataforma.
- **Autenticación Segura:** Utiliza tokens JWT (OAuth2) para proteger los endpoints y gestionar las sesiones de los usuarios en el dashboard.
- **Conexión Segura con Mercado Pago:** Provee un flujo OAuth2 completo para que los vendedores puedan conectar sus cuentas de Mercado Pago de forma segura y remota, sin compartir credenciales.
- **Gestión Centralizada de Tokens:** Almacena y gestiona de forma segura los `access_token` y `refresh_token` de cada vendedor en una base de datos central.
- **Auto-Refresco de Tokens:** Incluye una lógica proactiva que renueva automáticamente los tokens de Mercado Pago antes de que expiren, garantizando la operación continua del sistema.
- **API para Tótems:** Expone un endpoint seguro (`/api/v1/totems/token/{external_pos_id}`) para que los tótems soliciten las credenciales de pago que necesitan para operar.
- **Receptor de Webhooks:** Preparado para recibir notificaciones de pago en tiempo real desde Mercado Pago, validando la autenticidad de cada petición.
- **Dashboard Web:** Incluye una interfaz web simple (servida con Jinja2) para que los vendedores y administradores puedan gestionar sus cuentas, tótems y ver el historial de pagos.

---

## 3. Arquitectura y Tecnologías

- **Framework:** FastAPI
- **Base de Datos:** SQLAlchemy con soporte para MySQL (producción) y SQLite (desarrollo).
- **Autenticación:** Passlib (para hashing de contraseñas) y python-jose (para JWT).
- **Servidor:** Uvicorn.
- **Contenedorización:** Diseñado para ser desplegado fácilmente con Docker.

---

## 4. Instalación y Puesta en Marcha (Producción en Ubuntu)

Sigue estos pasos para desplegar el backoffice en un servidor Ubuntu.

### Paso 1: Preparar el Servidor

1.  **Instalar dependencias del sistema:**
    ```bash
    sudo apt update
    sudo apt install -y python3-venv python3-pip mysql-server
    ```
2.  **Instalar MySQL 8.4 (si es necesario):**
    Si la versión por defecto no es la 8.4, sigue los pasos detallados para instalarla desde los repositorios oficiales de MySQL. Esto puede implicar descargar el paquete `mysql-apt-config`, seleccionar la versión y ajustar las fuentes del repositorio si usas una versión de Ubuntu no-LTS.

3.  **Configurar y asegurar MySQL:**
    ```bash
    sudo mysql_secure_installation
    ```
    Luego, crea la base de datos y el usuario para la aplicación:
    ```sql
    CREATE DATABASE oem_backoffice;
    CREATE USER 'oem_user'@'localhost' IDENTIFIED BY 'tu_contraseña_segura';
    GRANT ALL PRIVILEGES ON oem_backoffice.* TO 'oem_user'@'localhost';
    FLUSH PRIVILEGES;
    EXIT;
    ```

### Paso 2: Desplegar la Aplicación

1.  **Clonar el repositorio:**
    ```bash
    git clone <URL_DE_TU_REPOSITORIO> OemTotemPark
    cd OemTotemPark/backoffice_app
    ```
2.  **Crear y activar el entorno virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Instalar dependencias de Python:**
    ```bash
    pip install -r requirements.txt
    ```

### Paso 3: Configurar las Variables de Entorno

1.  **Crear el archivo `.env`** dentro de la carpeta `backoffice_app`:
    ```bash
    nano .env
    ```
2.  **Añadir la configuración de producción:**
    ```ini
    # URL de la base de datos de producción
    DATABASE_URL="mysql+mysqlconnector://oem_user:tu_contraseña_segura@localhost/oem_backoffice"

    # Credenciales de tu aplicación de Mercado Pago
    MP_APP_ID="TU_APP_ID"
    MP_SECRET_KEY="TU_SECRET_KEY"
    MP_WEBHOOK_SECRET="TU_WEBHOOK_SECRET"

    # URL pública de tu backoffice para la redirección de OAuth
    MP_REDIRECT_URI="https://backoffice.oemspot.com.ar/mercadopago/connect"

    # Claves de seguridad (generar con `openssl rand -hex 32`)
    SECRET_KEY="UNA_CLAVE_SECRETA_PARA_JWT"
    TOTEM_API_KEY="UNA_CLAVE_SECRETA_PARA_LA_API_DE_TOTEMS"
    ```

### Paso 4: Ejecutar la Aplicación

Para pruebas, puedes ejecutarla directamente:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Para producción, se recomienda configurarla como un servicio `systemd` y usar un reverse proxy como Nginx para gestionar el tráfico y los certificados SSL.

---

## 5. Uso de la API

Una vez que el servidor está en marcha, puedes acceder a la documentación interactiva en `http://tu_servidor:8000/docs` para probar todos los endpoints.

1.  **Crea un Vendedor (Admin):** Usa `POST /api/v1/admin/sellers` para crear la primera cuenta de vendedor (y asignarle el rol de `admin`).
2.  **Inicia Sesión:** Usa `POST /token` para obtener un token de acceso.
3.  **Autoriza:** Usa el botón "Authorize" en la documentación para usar tu token en las peticiones protegidas.
4.  **Gestiona:** Ahora puedes usar el resto de los endpoints para gestionar tótems y vendedores.