# Requisitos del Sistema

## 1. Requisitos funcionales

### RF-01 — Diligenciamiento de encuestas
El sistema debe permitir a los usuarios autorizados diligenciar encuestas correspondientes a los proyectos a los que estén asignados.

### RF-02 — Registro de encuestas
El sistema debe permitir guardar y enviar las encuestas diligenciadas, incluyendo respuestas, usuario, fecha, hora y ubicación GPS.

### RF-03 — Revisión de encuestas
El sistema debe permitir a los usuarios con permisos suficientes consultar, revisar y corregir la información registrada.

### RF-04 — Control de acceso por proyecto
El sistema debe permitir el acceso a los proyectos y sus encuestas únicamente a los usuarios asignados a dichos proyectos.

### RF-05 — Trabajo sin conexión
El sistema debe permitir diligenciar y almacenar encuestas localmente cuando no exista conexión a Internet.

### RF-06 — Sincronización
El sistema debe sincronizar con el servidor las encuestas pendientes cuando el dispositivo recupere conectividad.

### RF-07 — Registro automático de fecha y hora
El sistema debe registrar automáticamente la fecha y hora de cada encuesta.

### RF-08 — Exportación de datos
El sistema debe permitir a los usuarios autorizados exportar resultados en formato Excel o CSV.

### RF-09 — Bloqueo por intentos fallidos
El sistema debe bloquear temporalmente una cuenta después de cinco intentos consecutivos de inicio de sesión fallidos.

## 2. Requisitos no funcionales

### RNF-01 — Seguridad de contraseñas
Las contraseñas no deben almacenarse en texto plano y deben protegerse mediante un mecanismo seguro de hashing.

### RNF-02 — Compatibilidad móvil
La plataforma debe ser utilizable desde dispositivos Android e iOS.

### RNF-03 — Diseño adaptable
La interfaz debe adaptarse a diferentes tamaños de pantalla.

### RNF-04 — Operación offline
La aplicación debe conservar localmente la información capturada cuando no exista conexión.

### RNF-05 — Integridad de datos
La plataforma debe evitar pérdida o duplicación de encuestas durante la sincronización.

### RNF-06 — Capacidad inicial
La plataforma debe contemplar más de 300 usuarios registrados.

### RNF-07 — Rendimiento
Las consultas normales del usuario deberían responder en un tiempo objetivo de hasta 3 segundos, sujeto a validación técnica posterior.