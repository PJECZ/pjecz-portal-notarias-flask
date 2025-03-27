"""
Modulos, vistas
"""

import json

from flask import Blueprint, render_template, request, url_for
from flask_login import login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string
from portal_notarias.blueprints.modulos.models import Modulo
from portal_notarias.blueprints.permisos.models import Permiso
from portal_notarias.blueprints.usuarios.decorators import permission_required

MODULO = "MODULOS"

modulos = Blueprint("modulos", __name__, template_folder="templates")


@modulos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@modulos.route("/modulos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Modulos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Modulo.query
    # Solo los modulos en Plataforma Can Mayor
    # consulta = consulta.filter_by(en_plataforma_portal_notarias=True)
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"], save_enie=True)
        if nombre != "":
            consulta = consulta.filter(Modulo.nombre.contains(nombre))
    # Ordenar y paginar
    registros = consulta.order_by(Modulo.nombre).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("modulos.detail", modulo_id=resultado.id),
                },
                "icono": resultado.icono,
                "en_navegacion": resultado.en_navegacion,
                "en_plataforma_portal_notarias": resultado.en_plataforma_portal_notarias,
                "en_plataforma_carina": resultado.en_plataforma_carina,
                "en_plataforma_hercules": resultado.en_plataforma_hercules,
                "en_plataforma_web": resultado.en_plataforma_web,
                "en_portal_notarias": resultado.en_portal_notarias,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@modulos.route("/modulos")
def list_active():
    """Listado de Modulos activos"""
    return render_template(
        "modulos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Módulos",
        estatus="A",
    )


@modulos.route("/modulos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Modulos inactivos"""
    return render_template(
        "modulos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Módulos inactivos",
        estatus="B",
    )


@modulos.route("/modulos/<int:modulo_id>")
def detail(modulo_id):
    """Detalle de un Modulo"""
    modulo = Modulo.query.get_or_404(modulo_id)
    return render_template("modulos/detail.jinja2", modulo=modulo)
