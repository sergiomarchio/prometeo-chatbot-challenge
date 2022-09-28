# [Prometeo chatbot challenge](https://joinignitecommunity.com/desafio-chatbot/)

[![en](https://img.shields.io/badge/lang-en-green.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-silver.svg)](README.es.md)

This project implements a chatbot that allows the user to make use of the Prometeo Open Banking API functionality, from an easy to use and friendly interface.

by [Sergio Marchio](https://serg.ink)


The chatbot will be available during the contest evaluation period in [TODO set url](https://)


## Test data

To log into a provider you can use the credentials available in [Prometeo docs](https://docs.prometeoapi.com/docs/introducci%C3%B3n-1).


## Setup

In order to run this project, you must

 - Create a secret.key file in the project root directory, with the django secure key in plain text format (can be generated with random characters, ideally with more than 50 characters and more than 5 unique characters).
 - To use the guest login feature, create a file named 'api.key' in the [chatbot](chatbot) directory, containing a valid Prometeo API key in plain text format.


### To run the server *locally*

Remove security settings **Warning:** this is only for running the project locally for debugging/testing purposes
 - In the project's [settings.py](/prometeo_chatbot/settings.py) file,
   - Set DEBUG to True
   - Comment ALLOWED_HOSTS, CSRF_COOKIE_SECURE, SESSION_COOKIE_SECURE, SECURE_SSL_REDIRECT settings


 - create virtual env and activate it
```
virtualenv prometeo
source prometeo/bin/activate
```

 - install required packages
```
pip install -r requirements.txt
```

 - From the app root directory, start the server in the desired port, e.g. 8080
```
python manage.py runserver 8080 
```

 - Now you can access the chatbot from your browser:
```
http://localhost:8080/
```


## Features

- Multi-language support based on browser settings (English and Spanish)
- Protection against CSRF attacks

- Prometeo operations
  - Provider listing
  - Provider login with required fields, including interactive login
  - Provider logout
  - User info
  - User accounts
  - Account movements
  - User cards
  - Card movements


## Possible improvements

- Increase testing coverage
- Improve display of movements (account and card)
- Export movements to csv and/or pdf
- Language selection from UI
