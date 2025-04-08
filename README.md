# pjecz-portal-notarias

Es un sistema web hecho en Flask para la entrega de Edictos.

## Configurar

Crear un archivo con las variables de entorno `.env`

```bash
# Flask, para SECRET_KEY use openssl rand -hex 24
FLASK_APP=portal_notarias.app
FLASK_DEBUG=1
SECRET_KEY=xxxxxxxx

# Database
DB_HOST=127.0.0.1
DB_PORT=8432
DB_NAME=pjecz_plataforma_web
DB_USER=xxxxxxxx
DB_PASS=xxxxxxxx
SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://xxxxxxxx:xxxxxxxx@127.0.0.1:8432/pjecz_plataforma_web"

# Google Cloud Storage
CLOUD_STORAGE_DEPOSITO=xxxxxxxx

# Clave INEGI del Estado de Coahuila de Zaragoza
ESTADO_CLAVE=05

# Host
HOST=http://127.0.0.1:5000

# Redis
REDIS_URL=redis://127.0.0.1:8379
TASK_QUEUE=pjecz_portal_notarias

# Salt sirve para cifrar el ID con HashID, debe ser igual en la API
SALT=xxxxxxxx

# Sendgrid para enviar mensajes via correo electronico
SENDGRID_API_KEY=SG.XXXXXXXXXXXXXXXXXXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
SENDGRID_FROM_EMAIL=XXXXXXX@XXXXX.XXX.XX

# Si esta en PRODUCTION se evita reiniciar la base de datos
DEPLOYMENT_ENVIRONMENT=develop
```

Crear un bash script para cargar las variables y el entorno virtual

```bash
if [ -f ~/.bashrc ]
then
    . ~/.bashrc
fi

if command -v figlet &> /dev/null
then
    figlet Portal de Notarias
else
    echo "== Portal de Notarias"
fi
echo

if [ -f .env ]
then
    echo "-- Variables de entorno"
    source .env && export $(sed '/^#/d' .env | cut -d= -f1)
    export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.gcp-api-keys/justicia-digital-gob-mx-perseo-diana.json"
    echo "   CLOUD_STORAGE_DEPOSITO: ${CLOUD_STORAGE_DEPOSITO}"
    echo "   DB_HOST: ${DB_HOST}"
    echo "   DB_PORT: ${DB_PORT}"
    echo "   DB_NAME: ${DB_NAME}"
    echo "   DB_USER: ${DB_USER}"
    echo "   DB_PASS: ${DB_PASS}"
    echo "   DEPLOYMENT_ENVIRONMENT: ${DEPLOYMENT_ENVIRONMENT}"
    echo "   ESTADO_CLAVE: ${ESTADO_CLAVE}"
    echo "   FLASK_APP: ${FLASK_APP}"
    echo "   GOOGLE_APPLICATION_CREDENTIALS: ${GOOGLE_APPLICATION_CREDENTIALS}"
    echo "   HOST: ${HOST}"
    echo "   REDIS_URL: ${REDIS_URL}"
    echo "   SALT: ${SALT}"
    echo "   SECRET_KEY: ${SECRET_KEY}"
    echo "   SQLALCHEMY_DATABASE_URI: ${SQLALCHEMY_DATABASE_URI}"
    echo "   TASK_QUEUE: ${TASK_QUEUE}"
    echo
    export PGHOST=$DB_HOST
    export PGPORT=$DB_PORT
    export PGDATABASE=$DB_NAME
    export PGUSER=$DB_USER
    export PGPASSWORD=$DB_PASS
fi

if [ -d .venv ]
then
    echo "-- Python Virtual Environment"
    source .venv/bin/activate
    echo "   $(python3 --version)"
    export PYTHONPATH=$(pwd)
    echo "   PYTHONPATH: ${PYTHONPATH}"
    echo
    echo "-- Poetry"
    export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
    echo "   $(poetry --version)"
    echo
    echo "-- Flask 127.0.0.1:5000"
    alias arrancar="flask run --port=5000"
    echo "   arrancar = flask run --port=5000"
    echo
    echo "-- RQ Worker ${TASK_QUEUE}"
    alias fondear="rq worker ${TASK_QUEUE}"
    echo "   fondear"
    echo
    if [ -f cli/app.py ]
    then
        echo "-- Ejecutar el CLI"
        alias cli="python3 ${PWD}/cli/app.py"
        echo "   cli --help"
        echo
    fi
fi

if [ -f .github/workflows/gcloud-app-deploy.yml ]
then
    echo "-- Si cambia pyproject.toml reconstruya requirements.txt para el deploy en GCP via GitHub Actions"
    echo "   poetry export -f requirements.txt --output requirements.txt --without-hashes"
    echo
fi
```
