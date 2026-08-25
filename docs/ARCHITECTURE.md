# Arquitectura del Sistema
 

## 1. Objetivo de la arquitectura

La arquitectura de Field Data Platform busca separar claramente las responsabilidades del sistema para facilitar su desarrollo, mantenimiento, seguridad y escalabilidad.

La plataforma estará compuesta inicialmente por:

- una interfaz adaptable para dispositivos móviles y navegadores;
- un backend encargado de las reglas de negocio y validaciones;
- una base de datos local para permitir trabajo sin conexión;
- una base de datos PostgreSQL para almacenar la información central;
- un mecanismo de sincronización entre el dispositivo y el servidor;
- un sistema de almacenamiento para imágenes y evidencias.

## 2. Componentes principales

### 2.1 Frontend

El frontend será la interfaz utilizada por los usuarios desde dispositivos móviles, tabletas o navegadores 

Sus responsabilidades principales serán:

- Mostrar formularios y proyectos disponibles; 
- Permitir iniciar sesión ;
- capturar información de encuestas;
- Guardar temporalmente datos cuando no exista conexión. ;
- Mostrar el estado de sincronización. ;
- Enviar información al backend cuando exista conectividad. ;

### 2.2 Backend./API

El backend será responsable de aplicar las reglas de negocio y proteger la información recibida desde los dispositivos.

Sus responsabilidades serán:

- autenticar usuarios. 
- Validar permisos y roles 
- comprobar acceso a proyectos. 
- Validar encuestas y respuestas.  
- Gestionar usuarios, proyectos y formularios. 
- Procesar sincronizaciones 
- registrar auditoría. 
- Comunicarse con PostgreSQL 
- exponer servicios mediante una API. 


### 2.3  Base de datos local. 

La base de datos local permitirá conservar información en el dispositivo cuando no exista conexión a Internet.

Sus responsabilidades serán:

- Almacenar encuestas pendientes 
-conservar formularios necesarios para trabajar offline. 
- Mantener identificadores UUID.
- Registrar el estado de sincronización. 
- Conservar los datos aunque la aplicación se cierre. 

### 2.4 Base de datos central. 

PostgreSQL. Almacenará la información persistente del sistema. 

Entre los datos principales serán. :

- Usuarios 
- roles. 
- Proyectos. 
- Asignaciones. 
- Formularios. 
- Versiones. 
- Campos. 
- Encuestas. 
- Respuestas 
- productos. 
- Establecimientos 
- auditoría. 

### 2.5 Almacenamiento de imágenes 

las fotografías YY evidencias se almacenarán fuera de las tablas principales de postgreSQL. 

La base de datos conservará una referencia o ruta hacia cada archivo.

# 3. Flujo de sincronización. 

La plataforma debe permitir que los usuarios continúen trabajando cuando no exista conexión a Internet .

### 3.1 creación de una encuesta sin conexión. 

Cuando el usuario complete una encuesta sin conectividad:

1. La aplicación generará un UUID para identificar la encuesta. 
2. La encuesta se almacenará en la base de datos local. 
3. Se registrarán las respuestas fecha, hora, ubicación y usuario 
4. la encuesta quedará con Estado pendiente. 
5. La información permannis irá disponible, aunque la aplicación se cierre. 

### 3.2 Recuperación de la conexión 

cuando el dispositivo Recuperé conectividad:

1. el mecanismo de sincronización buscará registros con estado pendiente. 
2. Enviar a luz registros al backend mediante la API. 
3. El backend autenticará al usuario. 
4. El backend validará permisos, proyecto formulario y datos recibidos. 
5. Sí, la información es válida, será almacenada por postgreSQL 
6. El servidor confirmará que la operación fue procesada. 
7. La aplicación cambiará al Estado local a sincronizada. 


### 3.3 Error durante la sincronización. 

Si ocurre un error:

1. La encuesta permanecerá almacenada localmente 
2. su estado cambiará a error o permanecerá pendiente según el tipo de fallo. 
3. El sistema registrará información sobre el error. 
4. La encuesta. Podrá volver a intentar sincronizarse posteriormente. 

### 3.4 Prevención de duplicados e idempotencia

Cada encuesta creada en el dispositivo tendrá un UUID único.

Cuando el backend reciba una encuesta durante la sincronización, verificará si ese UUID ya fue procesado.

Si el UUID no existe, la encuesta será validada y almacenada.

Si el UUID ya existe, el backend no creará una segunda encuesta y responderá indicando que el registro ya fue procesado.

Este mecanismo permitirá realizar reintentos de sincronización sin generar encuestas duplicadas.
