# [Prometeo chatbot challenge](https://joinignitecommunity.com/desafio-chatbot/)

[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-yellow.svg)](README.es.md)


Este proyecto implementa un chatbot que permite al usuario utilizar las funcionalidades de la API de Prometeo Open Banking, desde una interfaz amigable y fácil de usar.

by Sergio Marchio

visita my sitio web! [serg.ink](https://serg.ink)


El chatbot estará disponible durante la evaluación del desafío en [TODO set url](https://)


## Instalación

Para poder ejecutar el proyecto, debes primero:

 - Crear un archivo secret.key en la carpeta raíz del proyecto, con la clave segura de django en formato de texto plano (puede ser generada a partir de caracteres aleatorios, idealmente con más de 50 caracteres y más de 5 caracteres únicos.)
 - Para usar la caraterísitica de usuario invitado, crear un archivo con el nombre 'api.key' en el directorio [chatbot](chatbot), conteniendo una clave API de Prometeo válida, en formato de texto plano.

### Para ejecutar el servidor localmente

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

El bot soporta las siguientes operaciones en Prometeo:

- Listar los proveedores
- Iniciar sesión en un proveedor con los campos requeridos, incluyendo inicio de sesión interactivo
- Cerrar sesión en el proveedor
- Información del usuario
- Cuentas del usuario
- Tarjetas del usuario

