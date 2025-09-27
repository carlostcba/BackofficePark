# Back-Office API para OEM Totem Park

## 1. Descripción General

Esta aplicación es un backend desarrollado en **FastAPI** que sirve como sistema de gestión central para la plataforma OEM Totem Park. Proporciona una API RESTful para administrar vendedores (propietarios de estacionamientos) y sus tótems, además de manejar la integración y autenticación con Mercado Pago.

El proyecto también incluye un dashboard web simple (frontend) para que los vendedores puedan gestionar sus recursos.

---

## 2. Características Principales

- **Gestión de Vendedores:** Sistema de autenticación basado en JWT (login/logout) y registro de nuevos vendedores.
- **Gestión de Tótems (CRUD):** Endpoints para crear, leer, actualizar y eliminar tótems, asociándolos a un vendedor.
- **Integración con Mercado Pago:** Flujo de conexión OAuth2 para que los vendedores vinculen sus cuentas de Mercado Pago de forma segura.
- **API para Tótems:** Un endpoint seguro (`/api/v1/totems/token/{external_pos_id}`) para que los tótems físicos obtengan el token de acceso de su vendedor y puedan procesar pagos.
- **Auto-Refresco de Tokens:** Lógica para refrescar automáticamente los tokens de Mercado Pago que están a punto de expirar.
- **Dashboard Web:** Una interfaz de usuario desarrollada con HTML, CSS (Tailwind) y JavaScript para la gestión visual de la plataforma.
- **Documentación Automática:** Documentación interactiva de la API (generada por Swagger UI y ReDoc) disponible en los endpoints `/docs` y `/redoc`.

---

## 3. Instalación y Puesta en Marcha

Sigue estos pasos para levantar el entorno de desarrollo local.

### 3.1. Prerrequisitos

- Python 3.10+
- Un cliente de base de datos MySQL.

### 3.2. Instalación

1.  **Clona el repositorio** (si aún no lo has hecho).

2.  **Navega al directorio del back-office**:
    ```sh
    cd api-backoffice-totem
    ```

3.  **Crea y activa un entorno virtual**:
    ```sh
    # En Windows
    python -m venv venv
    .\venv\Scripts\activate

    # En macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **Instala las dependencias**:
    ```sh
    pip install -r requirements.txt
    ```

### 3.3. Configuración

1.  La configuración de la aplicación se gestiona en el archivo `settings.py`, que a su vez lee variables de entorno.
2.  Crea un archivo `.env` en la raíz de `/api-backoffice-totem` (puedes copiar y renombrar `.env.example` si existe).
3.  Rellena las variables de entorno necesarias, especialmente las credenciales de la base de datos y las claves de la API de Mercado Pago.

### 3.4. Ejecutar la Aplicación

Una vez que el entorno esté configurado, ejecuta el servidor con Uvicorn:

```sh
uvicorn api-backoffice-totem.main:app --reload
```

- `--reload`: Hace que el servidor se reinicie automáticamente cada vez que detecta un cambio en el código.

La aplicación estará disponible en **http://127.0.0.1:8000**.

---

## 4. Uso del Dashboard

1.  **Accede al Login:** Navega a `http://127.0.0.1:8000/`.
2.  **Crea una cuenta:** Si no tienes un usuario, puedes crear uno enviando una petición POST al endpoint `/sellers/` (puedes usar una herramienta como Postman, Insomnia o `curl`).
3.  **Inicia Sesión:** Usa las credenciales creadas para acceder al dashboard.
4.  **Conecta Mercado Pago:** Dentro del dashboard, si tu cuenta no está vinculada, verás un botón para conectar con Mercado Pago. Sigue el flujo para autorizar la aplicación.
5.  **Gestiona tus Tótems:** Una vez conectado, podrás añadir, editar y eliminar tus tótems desde la tabla correspondiente.
