🏋️‍♂️ Sistema de Gestión de Gimnasio (Backend & Cloud)
Este proyecto es una aplicación web integral para la gestión de un gimnasio, 
enfocada en la implementación de una arquitectura relacional segura y el uso de 
servicios en la nube para el alojamiento de bases de datos y aplicaciones.

Enlaces 🔗
* Aplicación en vivo: https://www.google.com/search?q=https://gimnasio-pro-web.onrender.com
* Aplicación estatica https://www.google.com/search?q=https://LuisDaniel-cmd.github.io/BDGimansio/

Herramientas 🛠
Lenguaje: Python 3.10
Framework: Flask
Base de Datos: PostgreSQL
Hosting DB: Neon Tech
Hosting App: Render
Conector Pyscopg2

🔐 Seguridad y Control de Acceso (DCL)
A diferencia de las aplicaciones tradicionales, la seguridad de este sistema se delega 
directamente al motor de la base de datos mediante Data Control Language (DCL). 
No dependemos únicamente de la lógica de programación, sino de los permisos de Postgr

Roles
Jefe (admin): Posee ALL PRIVILEGES. Puede gestionar miembros, clases, pagos y eliminar registros históricos.

Recepcionista: Posee permisos de INSERT, SELECT y UPDATE. Gestiona el día a día (altas y cobros) pero no puede borrar información.

Instructor: Permisos de SELECT limitado. Solo visualiza horarios y listas de alumnos. Bloqueado de toda información financiera.

📡 Flujo de Conexión y Arquitectura

Código Fuente: Almacenado en GitHub.
CI/CD: Render detecta automáticamente los cambios en la rama main y redespliega la app.
Variables de Entorno: Las credenciales de Neon (DATABASE_URL, HOST, etc.) se inyectan de forma segura en Render, evitando exponer claves en el código.
Conexión Dinámica: La aplicación abre un túnel seguro hacia Neon cada vez que se requiere una operación, utilizando psycopg2.

Desarrollado por 
Saavedra Duran Luis Daniel
Solano Flores Angelica.

Base de datos | ESCOM - IPN
