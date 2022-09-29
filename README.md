# [Prometeo chatbot challenge](https://joinignitecommunity.com/desafio-chatbot/)

[![en](https://img.shields.io/badge/lang-en-green.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-silver.svg)](README.es.md)

This project implements a chatbot that allows the user to make use of the Prometeo Open Banking API functionality, from an easy-to-use and friendly interface.

by Sergio Marchio


## Test data

To log into a provider you can use the credentials available in [Prometeo docs](https://docs.prometeoapi.com/docs/introducci%C3%B3n-1).


## Initial setup - extra files required

To run this project, you must create the file
 - `secret.key` in the root directory of the project, containing the django secure key in plain text format (ideally created with more than 50 random characters and more than 5 unique characters).
 
To use the guest login feature, you must create the file
- `api.key` in the [chatbot](chatbot) directory, containing a valid Prometeo API key in plain text format.


### To run the server *locally*

The project is configured by default for its local execution, for debugging/testing purposes

From the project's root directory, in the console:

 - Create virtual environment
`python -m venv prometeo`

 - Activate it

   - linux / MacOS:
   - `source prometeo/bin/activate`

   - Windows
   - `prometeo\Scripts\activate.bat`

 - install required packages
```
pip install -r requirements.txt
```

 - Start the server in the desired port, e.g. 8080
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

- Prometeo operations and `messages` to trigger them
  - Provider listing
    - `banks`
  - Provider login with required fields, including interactive login
    - `<provider name>`
  - Provider logout
    - `logout`
  - User info
    - `info`
  - User accounts
    - `accounts`
  - Account movements
    - `account <acount number> movements <date range>`
  - User cards
    - `cards`
  - Card movements
    - `card <acount number> movements <date range>`


## Possible improvements

- Increase testing coverage
- Improve display of movements (account and card)
- Export movements to csv and/or pdf
- Language selection from UI
