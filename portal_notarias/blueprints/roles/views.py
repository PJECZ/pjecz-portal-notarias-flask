"""
Roles, vistas
"""

import json

from flask import Blueprint, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string
from portal_notarias.blueprints.permisos.models import Permiso
from portal_notarias.blueprints.roles.models import Rol
from portal_notarias.blueprints.usuarios.decorators import permission_required

MODULO = "ROLES"

roles = Blueprint("roles", __name__, template_folder="templates")


@roles.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@roles.route("/roles/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Roles"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Rol.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"], save_enie=True)
        if nombre != "":
            consulta = consulta.filter(Rol.nombre.contains(nombre))
    # Ordenar y paginar
    registros = consulta.order_by(Rol.nombre).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("roles.detail", rol_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@roles.route("/roles")
def list_active():
    """Listado de Roles activos"""
    return render_template(
        "roles/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Roles",
        estatus="A",
    )


@roles.route("/roles/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Roles inactivos"""
    return render_template(
        "roles/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Roles inactivos",
        estatus="B",
    )


@roles.route("/roles/<int:rol_id>")
def detail(rol_id):
    """Detalle de un Rol"""
    rol = Rol.query.get_or_404(rol_id)
    return render_template("roles/detail.jinja2", rol=rol)
