"""
Permisos, vistas
"""

import json

from flask import Blueprint, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string
from portal_notarias.blueprints.modulos.models import Modulo
from portal_notarias.blueprints.permisos.models import Permiso
from portal_notarias.blueprints.roles.models import Rol
from portal_notarias.blueprints.usuarios.decorators import permission_required

MODULO = "PERMISOS"

permisos = Blueprint("permisos", __name__, template_folder="templates")


@permisos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@permisos.route("/permisos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Permisos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Permiso.query
    # Solo los modulos en Plataforma Can Mayor
    consulta = consulta.join(Modulo).filter(Modulo.en_plataforma_portal_notarias == True)
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(Permiso.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(Permiso.estatus == "A")
    if "modulo_id" in request.form:
        consulta = consulta.filter(Permiso.modulo_id == request.form["modulo_id"])
    if "rol_id" in request.form:
        consulta = consulta.filter(Permiso.rol_id == request.form["rol_id"])
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"], save_enie=True)
        if nombre != "":
            consulta = consulta.filter(Permiso.nombre.contains(nombre))
    if "nivel" in request.form:
        nivel = safe_string(request.form["nivel"], save_enie=True)
        if nivel != "":
            consulta = consulta.filter(Permiso.nivel == nivel)
    # Luego filtrar por columnas de otras tablas
    if "rol_nombre" in request.form:
        rol_nombre = safe_string(request.form["rol_nombre"], save_enie=True)
        if rol_nombre != "":
            consulta = consulta.join(Rol).filter(Rol.nombre.contains(rol_nombre))
    if "modulo_nombre" in request.form:
        modulo_nombre = safe_string(request.form["modulo_nombre"], save_enie=True)
        if modulo_nombre != "":
            consulta = consulta.filter(Modulo.nombre.contains(modulo_nombre))  # Antes se hizo el join(Modulo)
    # Ordenar y paginar
    registros = consulta.order_by(Permiso.nombre).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("permisos.detail", permiso_id=resultado.id),
                },
                "nivel": resultado.nivel_descrito,
                "modulo": {
                    "nombre": resultado.modulo.nombre,
                    "url": url_for("modulos.detail", modulo_id=resultado.modulo_id) if current_user.can_view("MODULOS") else "",
                },
                "rol": {
                    "nombre": resultado.rol.nombre,
                    "url": url_for("roles.detail", rol_id=resultado.rol_id) if current_user.can_view("ROLES") else "",
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@permisos.route("/permisos")
def list_active():
    """Listado de Permisos activos"""
    return render_template(
        "permisos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Permisos",
        estatus="A",
    )


@permisos.route("/permisos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Permisos inactivos"""
    return render_template(
        "permisos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Permisos inactivos",
        estatus="B",
    )


@permisos.route("/permisos/<int:permiso_id>")
def detail(permiso_id):
    """Detalle de un Permiso"""
    permiso = Permiso.query.get_or_404(permiso_id)
    return render_template("permisos/detail.jinja2", permiso=permiso)
