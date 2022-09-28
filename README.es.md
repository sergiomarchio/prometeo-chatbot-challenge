# [Prometeo chatbot challenge](https://joinignitecommunity.com/desafio-chatbot/)

[![en](https://img.shields.io/badge/lang-en-silver.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-green.svg)](README.es.md)


Este proyecto implementa un chatbot que permite al usuario utilizar las funcionalidades de la API de Prometeo Open Banking, desde una interfaz amigable y fácil de usar.

by [Sergio Marchio](https://serg.ink)


El chatbot estará disponible durante la evaluación del desafío en [TODO set url](https://)


## Datos de test

Para iniciar sesión en un banco puedes utilizar las credenciales disponibles en [Prometeo docs](https://docs.prometeoapi.com/docs/introducci%C3%B3n-1).


## Instalación

Para poder ejecutar el proyecto, debes primero:

 - Crear un archivo secret.key en la carpeta raíz del proyecto, con la clave segura de django en formato de texto plano (puede ser generada a partir de caracteres aleatorios, idealmente con más de 50 caracteres y más de 5 caracteres únicos).
 - Para usar la caraterística de usuario invitado, crear un archivo con el nombre 'api.key' en el directorio [chatbot](chatbot), conteniendo una API key de Prometeo válida, en formato de texto plano.


### Para ejecutar el servidor *localmente*

Desactivar configuración de seguridad **Cuidado:** esto es únicamente para ejecutar el proyecto de manera local, con el fines de debugging o testing
 - En el archivo [settings.py](/prometeo_chatbot/settings.py) del proyecto,
   - Definir DEBUG a True
   - Comentar las líneas ALLOWED_HOSTS, CSRF_COOKIE_SECURE, SESSION_COOKIE_SECURE, SECURE_SSL_REDIRECT


 - crear un entorno virtual y activarlo
```
virtualenv prometeo
source prometeo/bin/activate
```

 - instalar los paquetes requeridos
```
pip install -r requirements.txt
```

 - Desde el directorio raíz de la aplicación, iniciar el servidor en el puerto deseado, ej: 8080
```
python manage.py runserver 8080 
```

 - Ahora puedes acceder al chatbot desde tu navegador:
```
http://localhost:8080/
```


## Características

- Soporte para distintos idiomas en base a la configuración del navegador (Español e Inglés)
- Protección contra ataques CSRF

- Operaciones en Prometeo
  - Listar los proveedores
  - Iniciar sesión en un proveedor con los campos requeridos, incluyendo inicio de sesión interactivo
  - Cerrar sesión en el proveedor
  - Información del usuario
  - Cuentas del usuario
  - Movimientos de cuenta
  - Tarjetas del usuario
  - Movimientos de tarjeta


## Mejoras posibles

- Aumentar la cobertura de testing
- Mejorar la forma que se muestran los movimientos (cuenta y tarjeta)
- Exportar movimientos a csv y/o pdf
- Elección de idioma desde la interfaz
