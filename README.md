# Sistema de Control de Gastos Personales

Aplicación web desarrollada en Python con el microframework Flask para la gestión integral de finanzas personales. Permite a los usuarios registrarse de forma segura, administrar ingresos y egresos por categorías estandarizadas, visualizar balances financieros en tiempo real y consultar un historial filtrado.

---

## Tabla de Contenidos

1. [Propósito del Proyecto](#propósito-del-proyecto)
2. [Tecnologías Utilizadas](#tecnologías-utilizadas)
3. [Estructura del Repositorio](#estructura-del-repositorio)
4. [Requisitos Previos](#requisitos-previos)
5. [Instalación y Ejecución Local](#instalación-y-ejecución-local)
6. [Preparación de la Base de Datos](#preparación-de-la-base-de-datos)
7. [Variables de Entorno y Seguridad](#variables-de-entorno-y-seguridad)
8. [Acceso Local y Despliegue en Producción](#acceso-local-y-despliegue-en-producción)
9. [Endpoints Principales](#endpoints-principales)
10. [Funcionalidades y Limitaciones](#funcionalidades-y-limitaciones)

---

## Propósito del Proyecto

Brindar una herramienta web ligera, accesible y reproducible que facilite el seguimiento diario de ingresos y gastos personales, garantizando la integridad y validación de los datos ingresados, persistencia relacional y separación estricta de registros por usuario autenticado.

---

## Tecnologías Utilizadas

* **Backend:** Python 3.13.14, Flask 3.1.3, Flask-Login, Werkzeug.
* **Base de Datos:** SQLite 3 (`gastos.db`) con resolución de ruta absoluta.
* **Frontend:** HTML5, Pico CSS, plantillas Jinja2 y JavaScript ES6 (Fetch API).
* **Servidor de Producción:** WSGI nativo de PythonAnywhere con entorno virtual aislado (`venv`).
* **Control de Versiones:** Git y GitHub.

---

## Estructura del Repositorio

```text
Control-de-Gastos/
├── control_gastos/
│   ├── templates/
│   │   ├── index.html       # Panel principal, formulario dinámico e historial
│   │   ├── login.html       # Vista de inicio de sesión
│   │   ├── registro.html    # Vista de registro de nuevos usuarios
│   │   └── editar.html      # Formulario de edición de registros
│   ├── app.py               # Lógica del servidor, rutas web, API REST y SQLite
│   └── gastos.db            # Base de datos SQLite (generada al iniciar)
├── requirements.txt         # Dependencias del proyecto
├── .env.example             # Ejemplo de variables de entorno sin secretos
├── .gitignore               # Exclusión de archivos temporales y entornos virtuales
└── README.md                # Documentación principal del proyecto
```

---

## Requisitos Previos

* Python 3.10 o superior (desarrollado y probado en Python 3.13.14).
* Git instalado en el sistema.
* Gestor de paquetes `pip`.

---

## Instalación y Ejecución Local

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/dunkelsein/Control-de-Gastos.git
   cd Control-de-Gastos
   ```

2. **Crear y activar un entorno virtual:**
   * En Windows:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   * En Linux / macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instalar las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar las variables de entorno:**
   Copiar el archivo `.env.example` como `.env` y asignar una clave secreta local:
   ```bash
   cp .env.example .env
   ```

5. **Iniciar el servidor local:**
   ```bash
   python control_gastos/app.py
   ```

---

## Preparación de la Base de Datos

La base de datos SQLite (`gastos.db`) no requiere configuración manual externa. Al arrancar la aplicación (tanto en entorno local como en el servidor WSGI de producción), la función `inicializar_db()` verifica y crea automáticamente las tablas necesarias (`usuarios` y `transacciones`) mediante rutas absolutas (`os.path.abspath`), evitando errores por rutas relativas en despliegue.

---

## Variables de Entorno y Seguridad

Para proteger la información sensible, el archivo `.env` está excluido del repositorio mediante `.gitignore`. El archivo `.env.example` documenta las variables necesarias:

```env
SECRET_KEY=cambiar_por_una_clave_secreta_segura
FLASK_ENV=development
```

* Las contraseñas de los usuarios se encriptan antes de almacenarse mediante `generate_password_hash()` de Werkzeug.
* Las rutas privadas están protegidas mediante el decorador `@login_required` de Flask-Login.

---

## Acceso Local y Despliegue en Producción

* **Acceso Local:** Una vez iniciado el servidor, abrir en el navegador:
  `http://127.0.0.1:5000`
* **Acceso Desplegado (Producción):** La aplicación se encuentra publicada y operativa en PythonAnywhere bajo entorno virtual dedicado:
  `https://dunkel.pythonanywhere.com`

### Actualización en Producción (PythonAnywhere)

Para reflejar nuevos cambios subidos al repositorio de GitHub en el entorno desplegado:
1. Acceder a la consola Bash en PythonAnywhere dentro de `/home/Dunkel/Control-de-Gastos`.
2. Ejecutar `git pull origin main`.
3. Ingresar a la pestaña **Web** y presionar el botón **Reload** para reiniciar el servidor WSGI.

---

## Endpoints Principales

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/login` | Muestra el formulario de inicio de sesión. |
| `POST` | `/login` | Autentica las credenciales del usuario e inicia sesión. |
| `GET` | `/registro` | Muestra el formulario de registro de usuario. |
| `POST` | `/registro` | Crea un nuevo usuario con contraseña encriptada. |
| `GET` | `/` | Renderiza el panel principal con movimientos y categorías del usuario. |
| `POST` | `/` | Registra un nuevo ingreso o gasto validando campos obligatorios. |
| `GET` | `/editar/<id>` | Carga el formulario de edición para una transacción específica. |
| `POST` | `/editar/<id>` | Actualiza los datos de una transacción existente. |
| `POST` | `/eliminar/<id>` | Elimina un registro perteneciente al usuario autenticado. |
| `GET` | `/api/resumen` | Retorna en formato JSON los totales de ingresos, gastos y saldo actual. |
| `GET` | `/api/transacciones` | Lista las transacciones del usuario en formato JSON (`HTTP 200`). |
| `POST` | `/api/transacciones` | Crea una transacción vía API (`HTTP 201`) o devuelve error de validación (`HTTP 400`). |

---

## Funcionalidades y Limitaciones

### Funcionalidades Implementadas

* Registro e inicio de sesión seguro con gestión de sesiones por usuario.
* Creación, lectura, edición y eliminación (CRUD) de movimientos financieros.
* Selectores dependientes dinámicos que filtran las categorías disponibles según el tipo de movimiento seleccionado (Ingreso o Gasto).
* Validación de campos obligatorios tanto en cliente (HTML5/JavaScript) como en servidor (`HTTP 400 Bad Request`).
* Cálculo dinámico del balance financiero mediante consumo asíncrono de API REST (`fetch`).

### Limitaciones y Mejoras Futuras

* **Base de datos:** El uso de SQLite es óptimo para entornos académicos y de baja/mediana concurrencia; para escalamiento multiusuario masivo a futuro se contempla migrar a PostgreSQL.
* **Exportación de reportes:** Como mejora futura se planifica incorporar la descarga de balances mensuales en formatos CSV y PDF, así como filtros por rango de fechas.
