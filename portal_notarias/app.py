"""
Flask App
"""

import rq
from flask import Flask
from redis import Redis

from config.settings import Settings
from portal_notarias.blueprints.autoridades.views import autoridades
from portal_notarias.blueprints.bitacoras.views import bitacoras
from portal_notarias.blueprints.distritos.views import distritos
from portal_notarias.blueprints.edictos.views import edictos
from portal_notarias.blueprints.edictos_acuses.views import edictos_acuses
from portal_notarias.blueprints.entradas_salidas.views import entradas_salidas
from portal_notarias.blueprints.modulos.views import modulos
from portal_notarias.blueprints.permisos.views import permisos
from portal_notarias.blueprints.roles.views import roles
from portal_notarias.blueprints.sistemas.views import sistemas
from portal_notarias.blueprints.tareas.views import tareas
from portal_notarias.blueprints.usuarios.models import Usuario
from portal_notarias.blueprints.usuarios.views import usuarios
from portal_notarias.blueprints.usuarios_roles.views import usuarios_roles
from portal_notarias.extensions import csrf, database, login_manager, moment


def create_app():
    """Crear app"""
    # Definir app
    app = Flask(__name__, instance_relative_config=True)

    # Cargar la configuración
    app.config.from_object(Settings())

    # Redis
    app.redis = Redis.from_url(app.config["REDIS_URL"])
    app.task_queue = rq.Queue(app.config["TASK_QUEUE"], connection=app.redis, default_timeout=3000)

    # Registrar blueprints
    app.register_blueprint(autoridades)
    app.register_blueprint(bitacoras)
    app.register_blueprint(distritos)
    app.register_blueprint(edictos)
    app.register_blueprint(edictos_acuses)
    app.register_blueprint(entradas_salidas)
    app.register_blueprint(modulos)
    app.register_blueprint(permisos)
    app.register_blueprint(roles)
    app.register_blueprint(sistemas)
    app.register_blueprint(tareas)
    app.register_blueprint(usuarios)
    app.register_blueprint(usuarios_roles)

    # Inicializar extensiones
    extensions(app)

    # Inicializar autenticación
    authentication(Usuario)

    # Entregar app
    return app


def extensions(app):
    """Inicializar extensiones"""
    csrf.init_app(app)
    database.init_app(app)
    login_manager.init_app(app)
    moment.init_app(app)
    # socketio.init_app(app)


def authentication(user_model):
    """Inicializar Flask-Login"""
    login_manager.login_view = "usuarios.login"

    @login_manager.user_loader
    def load_user(uid):
        return user_model.query.get(uid)
