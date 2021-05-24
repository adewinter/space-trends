# django-base

# Project structure
`spacetrends` is a basic django app within the djano project named `mysite`.  To create a new Django app run
```
python manage.py startapp [app_name]
```

# Setup
* Install [pipenv](https://pypi.org/project/pipenv/)
* create a `.env` file by copying env.example in the root of this folder.  Pipenv will auto load the key=value pairs as env vars.
* from the root of this repo run
```
pipenv install
```
* Eventually you'll want to set the value for `ALLOWED_HOSTS` in `mysite/settings.py`

# Usage
run
```
python manage.py runserver
```
To kick off a dev server on your local machine