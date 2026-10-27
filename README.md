# Field Data Platform

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=111)
![TypeScript](https://img.shields.io/badge/TypeScript-6-3178C6?logo=typescript&logoColor=white)
![PWA](https://img.shields.io/badge/PWA-Offline%20Ready-5A0FC8?logo=pwa&logoColor=white)

**Field Data Platform** es una aplicación web full-stack orientada a la captura, administración y sincronización de información en campo. Permite gestionar proyectos, usuarios, formularios dinámicos y encuestas, incluyendo escenarios de trabajo sin conexión y sincronización posterior con el servidor.

El proyecto fue construido como una solución de ingeniería de software de extremo a extremo, con énfasis en **seguridad, control de acceso, operación offline, trazabilidad e integridad de datos**.

---

## Funcionalidades principales

- Autenticación mediante JWT.
- Contraseñas protegidas con hashing seguro.
- Bloqueo temporal de cuentas después de intentos fallidos de inicio de sesión.
- Recuperación administrativa de acceso para roles autorizados.
- Gestión de usuarios y roles.
- Asignación de usuarios a proyectos.
- Control de acceso basado en rol y proyecto.
- Creación, edición, activación e inactivación de proyectos.
- Eliminación definitiva de proyectos mediante confirmaciones reforzadas.
- Constructor de formularios dinámicos.
- Versionado de formularios con estados borrador, publicado y archivado.
- Campos configurables y opciones para preguntas de selección.
- Diligenciamiento de encuestas desde navegador o dispositivo móvil.
- Registro automático de fecha y hora.
- Captura de ubicación cuando el navegador lo permite.
- Almacenamiento local de encuestas mediante IndexedDB/Dexie.
- Trabajo offline y sincronización al recuperar conectividad.
- Uso de UUID para evitar duplicados durante reintentos de sincronización.
- Consulta, revisión y corrección de encuestas.
- Historial de correcciones.
- Exportación de resultados a CSV y XLSX.
- Interfaz responsive.
- Aplicación instalable como PWA.
- Suite automatizada de pruebas para autenticación, acceso, sincronización, recuperación de contraseña, capacidad y rendimiento.

---

## Arquitectura

```mermaid
flowchart LR
    U[Usuario] --> F[React + TypeScript]
    F --> L[(IndexedDB / Dexie)]
    F -->|HTTP / JWT| A[FastAPI]
    A --> S[SQLAlchemy]
    S --> P[(PostgreSQL)]
    A --> E[CSV / XLSX]

    L -->|Sincronización| A
```

La solución está separada en cuatro capas principales:

- **Frontend:** React, TypeScript y Vite.
- **API:** FastAPI con autenticación y reglas de negocio.
- **Persistencia central:** PostgreSQL mediante SQLAlchemy.
- **Persistencia local:** IndexedDB mediante Dexie para operación offline.

La evolución del esquema de base de datos se gestiona con **Alembic**.

Documentación adicional:

- [Arquitectura del sistema](docs/ARCHITECTURE.md)
- [Requisitos funcionales y no funcionales](docs/REQUIREMENTS.md)

---

## Stack tecnológico

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Psycopg
- PyJWT
- Argon2 / pwdlib
- OpenPyXL

### Frontend

- React
- TypeScript
- Vite
- Axios
- React Router
- Dexie
- IndexedDB
- vite-plugin-pwa

### Calidad y pruebas

- Pytest
- FastAPI TestClient
- Oxlint
- TypeScript compiler
- Git / GitHub

---

## Estructura del proyecto

```text
field-data-platform/
├── alembic/              # Migraciones de base de datos
├── backend/
│   ├── routers/          # Endpoints de la API
│   ├── schemas/          # Modelos de entrada y salida
│   ├── database.py       # Configuración de SQLAlchemy
│   ├── main.py           # Aplicación FastAPI
│   ├── models.py         # Modelos ORM
│   └── security.py       # JWT, hashing y autorización
├── docs/
│   ├── ARCHITECTURE.md
│   └── REQUIREMENTS.md
├── frontend/
│   └── src/
│       ├── api/
│       ├── pages/
│       ├── types/
│       └── ...
├── tests/                # Pruebas automatizadas
├── requirements.txt
└── requirements-dev.txt
```

---

## Seguridad y autorización

La plataforma implementa autenticación basada en JWT y control de acceso por roles.

Roles de control:

- Director
- Jefe Nacional
- Coordinador
- Analista

Roles operativos:

- Auxiliar
- Vendedor
- Mercaimpulso

Además del rol, el sistema valida la asignación del usuario al proyecto correspondiente antes de permitir el acceso a su información.

Las contraseñas no se almacenan en texto plano y el sistema incorpora bloqueo temporal de cuenta por intentos fallidos.

---

## Operación offline

Una de las características principales del proyecto es el soporte de trabajo sin conexión.

Cuando no existe conectividad:

1. El formulario y la información necesaria permanecen disponibles localmente.
2. La encuesta se guarda en IndexedDB.
3. Se genera un UUID único.
4. La encuesta queda pendiente de sincronización.
5. Cuando vuelve la conectividad, el frontend intenta enviarla al backend.
6. El backend comprueba el UUID para evitar registros duplicados.

Este flujo permite reintentar sincronizaciones sin crear múltiples copias de una misma encuesta.

---

## Instalación local

### 1. Clonar el repositorio

```bash
git clone https://github.com/carloscifuentesingsoft1560-cyber/field-data-platform.git
cd field-data-platform
```

### 2. Crear y activar el entorno virtual

En Windows:

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias del backend

```powershell
pip install -r requirements.txt
```

Para desarrollo y pruebas:

```powershell
pip install -r requirements-dev.txt
```

### 4. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
DATABASE_URL=postgresql+psycopg://USUARIO:CONTRASENA@localhost:5432/field_data_platform
JWT_SECRET_KEY=CLAVE_SECRETA_SEGURA
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

> El archivo `.env` está excluido del repositorio y no debe contener credenciales públicas.

### 5. Ejecutar migraciones

```powershell
alembic upgrade head
```

### 6. Iniciar el backend

```powershell
python -m uvicorn backend.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Documentación interactiva:

```text
http://127.0.0.1:8000/docs
```

### 7. Instalar e iniciar el frontend

En otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

Aplicación:

```text
http://localhost:5173
```

---

## Pruebas y calidad

Ejecutar pruebas del backend:

```powershell
python -m pytest -q
```

Validar frontend:

```powershell
cd frontend
npm run lint
npm run build
```

La suite cubre, entre otros escenarios:

- autenticación;
- bloqueo de acceso;
- permisos por proyecto;
- sincronización idempotente de encuestas;
- recuperación administrativa de contraseña;
- capacidad y rendimiento.

---

## Requisitos de negocio implementados

El proyecto contempla requisitos funcionales relacionados con:

- diligenciamiento y registro de encuestas;
- revisión y corrección;
- acceso restringido por proyecto;
- operación sin conexión;
- sincronización automática;
- fecha y hora;
- exportación;
- bloqueo de cuentas.

También se han trabajado requisitos no funcionales de seguridad, diseño responsive, persistencia offline, integridad de datos, capacidad y rendimiento.

Consulta el detalle en [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md).

---

## Estado actual

**MVP funcional en evolución.**

Las funcionalidades principales de captura, administración, seguridad, sincronización, revisión y exportación se encuentran implementadas. El proyecto continúa evolucionando en pruebas, despliegue, experiencia de usuario y endurecimiento para un entorno productivo.

---

## Objetivo del proyecto

Además de resolver un caso real de captura de información en campo, este repositorio demuestra experiencia práctica en:

- diseño y consumo de APIs REST;
- modelado relacional;
- autenticación y autorización;
- migraciones de base de datos;
- aplicaciones React con TypeScript;
- PWA y almacenamiento offline;
- sincronización e idempotencia;
- pruebas automatizadas;
- control de versiones con Git;
- desarrollo full-stack.

---

## Autor

**Carlos Eduardo Cifuentes Sanabria**  
Ingeniería de Software

GitHub: [@carloscifuentesingsoft1560-cyber](https://github.com/carloscifuentesingsoft1560-cyber)
