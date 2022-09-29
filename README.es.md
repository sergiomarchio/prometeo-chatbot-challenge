# [Prometeo chatbot challenge](https://joinignitecommunity.com/desafio-chatbot/)

[![en](https://img.shields.io/badge/lang-en-silver.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-green.svg)](README.es.md)


Este proyecto implementa un chatbot que permite al usuario utilizar las funcionalidades de la API de Prometeo Open Banking, desde una interfaz amigable y fácil de usar.

by Sergio Marchio


## Datos de test

Para iniciar sesión en un banco puedes utilizar las credenciales disponibles en [Prometeo docs](https://docs.prometeoapi.com/docs/introducci%C3%B3n-1).


## Configuración inicial - archivos extra requeridos

Para ejecutar el proyecto, debes crear el archivo
 - `secret.key` en el directorio raíz del proyecto (donde se encuentra el archivo [manage.py](manage.py)), conteniendo la clave segura de django en formato de texto plano (idealmente generada con más de 50 caracteres aleatorios y más de 5 caracteres únicos).
 
Para usar la caraterística de usuario invitado, debes crear el archivo
- `api.key` en el directorio [chatbot](chatbot), conteniendo una API key de Prometeo válida, en formato de texto plano.


### Para ejecutar el servidor *localmente*

El proyecto ya está configurado por defecto para su ejecución local, con fines de debugging o testing.

Desde el directorio raíz del proyecto, en la consola:

 - Crear un entorno virtual
`python -m venv prometeo`

 - Activarlo

   - linux / MacOS:
   - `source prometeo/bin/activate`

   - Windows
   - `prometeo\Scripts\activate.bat`

 - instalar los paquetes requeridos
```
pip install -r requirements.txt
```

 - Iniciar el servidor en el puerto deseado, ej.: 8080
```
python manage.py runserver 8080 
```

 - Ahora puedes acceder al chatbot desde tu navegador:
```
http://localhost:8080/
```


## Características

- Soporte para distintos idiomas dependiendo de la configuración del navegador (Español e Inglés)
- Protección contra ataques CSRF

- Operaciones en Prometeo y `mensajes` para relizarlas
  - Listar los proveedores
    - `bancos`
  - Iniciar sesión en un proveedor con los campos requeridos, incluyendo inicio de sesión interactivo
    - `<nombre del banco>`
  - Cerrar sesión en el proveedor
    - `salir`
  - Información del usuario
    - `info`
  - Cuentas del usuario
    - `cuentas`
  - Movimientos de cuenta
    - `cuenta <acount number> movimentos <date range>`
  - Tarjetas del usuario
    - `tarjetas`
  - Movimientos de tarjeta
    - `tarjeta <acount number> movimentos <date range>`


## Mejoras posibles

- Aumentar la cobertura de testing
- Mejorar la forma que se muestran los movimientos (cuenta y tarjeta)
- Exportar movimientos a csv y/o pdf
- Elección de idioma desde la interfaz
