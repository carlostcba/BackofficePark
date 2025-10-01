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

## 3. Instalación y Puesta en Marcha (Desarrollo Local)

Sigue estos pasos para levantar el entorno de desarrollo local.

### 3.1. Prerrequisitos

- Python 3.10+
- Un cliente de base de datos MySQL (o SQLite para desarrollo).

### 3.2. Instalación

1.  **Clona el repositorio** (si aún no lo has hecho).

2.  **Navega al directorio del back-office**:
    ```sh
    cd backoffice_app
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
2.  Crea un archivo `.env` en la raíz de `/backoffice_app` (puedes copiar y renombrar `.env.example` si existe).
3.  Rellena las variables de entorno necesarias, especialmente las credenciales de la base de datos y las claves de la API de Mercado Pago.

### 3.4. Ejecutar la Aplicación

Una vez que el entorno esté configurado, ejecuta el servidor con Uvicorn:

```sh
uvicorn main:app --reload
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

---

## 5. Despliegue en Servidor Ubuntu (Producción)

Esta sección detalla los pasos para desplegar la aplicación en un servidor Ubuntu 24.04 LTS con MySQL 8.4.x y ejecutarla como un servicio `systemd`.

### 5.1. Prerrequisitos del Servidor

- Servidor con Ubuntu 24.04 LTS (Noble Numbat).
- Acceso `sudo`.
- Git instalado.

### 5.2. Instalación de MySQL 8.4.x

1.  **Purgar cualquier instalación de MySQL existente (si la hay):**
    ```bash
    sudo systemctl stop mysql
    sudo apt-get purge mysql-server mysql-client mysql-common mysql-server-core-* mysql-client-core-*
    sudo apt-get autoremove
    sudo apt-get autoclean
    ```

2.  **Instalar MySQL 8.4.x:**
    *   **Descarga el Repositorio Oficial de MySQL:**
        ```bash
        wget https://dev.mysql.com/get/mysql-apt-config_0.8.34-1_all.deb
        ```
    *   **Instala el Paquete de Configuración:**
        ```bash
        sudo dpkg -i mysql-apt-config_0.8.34-1_all.deb
        ```
    *   **Selecciona la Versión de MySQL (en la pantalla azul):**
        *   En la pantalla azul, selecciona **"MySQL Server & Cluster"** y presiona `Enter`.
        *   Luego, selecciona **`mysql-8.4`** y presiona `Enter`.
        *   Finalmente, selecciona **"Ok"** y presiona `Enter`.
    *   **Corrige el Repositorio para Ubuntu "Noble" (24.04 LTS):**
        *   Abre el archivo de configuración:
            ```bash
            sudo nano /etc/apt/sources.list.d/mysql.list
            ```
        *   En todas las líneas donde veas la palabra `noble`, **reemplázala por `jammy`**.
        *   Guarda y cierra el archivo (`Ctrl+X`, `Y`, `Enter`).
    *   **Instala la dependencia `libaio1` manualmente:**
        ```bash
        wget http://archive.ubuntu.com/ubuntu/pool/main/liba/libaio/libaio1_0.3.112-13build1_amd64.deb
        sudo dpkg -i libaio1_0.3.112-13build1_amd64.deb
        # Si hay errores de dependencias, intenta:
        # sudo apt --fix-broken install
        ```
    *   **Actualiza los Repositorios e Instala `mysql-server`:**
        ```bash
        sudo apt update
        sudo apt install -y mysql-server
        ```

3.  **Verificar la Versión Instalada:**
    ```bash
    mysql --version
    ```
    Debería mostrar `8.4.x`.

4.  **Configurar y Asegurar MySQL:**
    ```bash
    sudo mysql_secure_installation
    ```
    (Sigue las instrucciones para establecer la contraseña de root y opciones de seguridad).

    Ahora, crea la base de datos y el usuario para la aplicación:
    ```bash
    sudo mysql
    # Dentro de la consola de MySQL, ejecuta:
    CREATE DATABASE oem_backoffice;
    CREATE USER 'oem_user'@'localhost' IDENTIFIED BY 'Oem2017*';
    GRANT ALL PRIVILEGES ON oem_backoffice.* TO 'oem_user'@'localhost';
    FLUSH PRIVILEGES;
    EXIT;
    ```

### 5.3. Despliegue de la Aplicación

1.  **Clonar el Repositorio:**
    ```bash
    # Navega a la ubicación deseada en tu servidor (ej. /home/tu_usuario/)
    git clone https://github.com/carlostcba/TotemPark.git
    cd TotemPark
    ```

2.  **Crear Entorno Virtual e Instalar Dependencias:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configurar el Archivo `.env` de Producción:**
    *   Crea el archivo `backoffice_app/.env` con el siguiente contenido. **Rellena los valores con tus datos de producción.**
    ```ini
    # --- Base de Datos de Producción ---
    DATABASE_URL="mysql+mysqlconnector://oem_user:tu_contraseña_segura@localhost/oem_backoffice"

    # --- Credenciales de Mercado Pago (Producción) ---
    MP_APP_ID="1057832979253760"
    MP_SECRET_KEY="yr3BZpEzW01jNXBl8K9HtjrQVDCT5KHs"

    # --- URL de Redirección Permanente ---
    MP_REDIRECT_URI="https://backoffice.oemspot.com.ar/mercadopago/connect"

    # --- Clave de Seguridad (Genera una nueva para producción) ---
    SECRET_KEY="9706d7d7090e107dd87f7283ff5a7f8039074b39c6050cd6f77450529db861bc"
    ```

4.  **Actualizar el Panel de Mercado Pago:**
    *   Ve a la configuración de tu aplicación en Mercado Pago y en "URLs de redireccionamiento", pon la URL definitiva: `https://backoffice.oemspot.com.ar/mercadopago/connect`.

### 5.4. Ejecutar como un Servicio Permanente (systemd)

Para que la aplicación se ejecute siempre, incluso si el servidor se reinicia, la configuraremos como un servicio del sistema.

1.  **Crea el archivo de servicio:**
    ```bash
    sudo nano /etc/systemd/system/oem-backoffice.service
    ```

2.  **Pega el siguiente contenido dentro del editor.** Asegúrate de cambiar `/ruta/absoluta/a/OemTotemPark` por la ruta real donde clonaste el proyecto y `tu_usuario_de_ubuntu` por tu nombre de usuario en Ubuntu.
    ```ini
    [Unit]
    Description=OEM Totem Park Backoffice Service
    After=network.target

    [Service]
    User=tu_usuario_de_ubuntu  # Cambia esto por tu nombre de usuario en Ubuntu
    Group=www-data
    WorkingDirectory=/ruta/absoluta/a/OemTotemPark/backoffice_app
    ExecStart=/ruta/absoluta/a/OemTotemPark/backoffice_app/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```
    *   Guarda y cierra el archivo (`Ctrl+X`, `Y`, `Enter`).

3.  **Activa y arranca el servicio:**
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable oem-backoffice.service
    sudo systemctl start oem-backoffice.service
    ```

4.  **Verifica el estado para asegurarte de que todo está corriendo sin errores:**
    ```bash
    sudo systemctl status oem-backoffice.service
    ```

¡Y listo! Con estos pasos, tu aplicación estará corriendo en producción de forma robusta y permanente, servida a través de tu proxy en la URL `https://backoffice.oemspot.com.ar`.