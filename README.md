# django-base

# Project structure
`timezones` is a basic django app within the djano project named `mysite`.  To create a new Django app run
```
python manage.py startapp [app_name]
```

# Setup
* Install [pipenv](https://pypi.org/project/pipenv/)
* create a `.env` file in the root of this folder.  Pipenv will auto load the key=value pairs as env vars.
* from the root of this repo run
```
pipenv install
```

# Usage
run
```
python manage.py runserver
```
To kick off a dev server on your local machine