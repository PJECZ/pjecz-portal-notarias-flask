"""
Autoridades, vistas
"""

import json

from flask import Blueprint, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_clave, safe_message, safe_string
from portal_notarias.blueprints.autoridades.models import Autoridad
from portal_notarias.blueprints.distritos.models import Distrito
from portal_notarias.blueprints.permisos.models import Permiso
from portal_notarias.blueprints.usuarios.decorators import permission_required

MODULO = "AUTORIDADES"

autoridades = Blueprint("autoridades", __name__, template_folder="templates")


@autoridades.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@autoridades.route("/autoridades/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Autoridades"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Autoridad.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(Autoridad.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(Autoridad.estatus == "A")
    if "distrito_id" in request.form:
        consulta = consulta.filter(Autoridad.distrito_id == request.form["distrito_id"])
    if "clave" in request.form:
        try:
            clave = safe_clave(request.form["clave"])
            if clave != "":
                consulta = consulta.filter(Autoridad.clave.contains(clave))
        except ValueError:
            pass
    if "descripcion" in request.form:
        descripcion = safe_string(request.form["descripcion"], save_enie=True)
        if descripcion != "":
            consulta = consulta.filter(Autoridad.descripcion.contains(descripcion))
    # Luego filtrar por columnas de otras tablas
    if "distrito_nombre" in request.form:
        distrito_nombre = safe_string(request.form["distrito_nombre"], save_enie=True)
        if distrito_nombre != "":
            consulta = consulta.join(Distrito).filter(Distrito.nombre.contains(distrito_nombre))
    # Ordenar y paginar
    registros = consulta.order_by(Autoridad.clave).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "clave": resultado.clave,
                    "url": url_for("autoridades.detail", autoridad_id=resultado.id),
                },
                "descripcion_corta": resultado.descripcion_corta,
                "distrito_clave": resultado.distrito.clave,
                "distrito_nombre_corto": resultado.distrito.nombre_corto,
                "es_extinto": "EXTINTO" if resultado.es_extinto else "",
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@autoridades.route("/autoridades")
def list_active():
    """Listado de Autoridades activas"""
    return render_template(
        "autoridades/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Autoridades",
        estatus="A",
    )


@autoridades.route("/autoridades/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Autoridades inactivas"""
    return render_template(
        "autoridades/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Autoridades inactivas",
        estatus="B",
    )


@autoridades.route("/autoridades/<int:autoridad_id>")
def detail(autoridad_id):
    """Detalle de una Autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    return render_template("autoridades/detail.jinja2", autoridad=autoridad)


@autoridades.route("/autoridades/select_json/<int:distrito_id>", methods=["GET", "POST"])
def query_autoridades_json(distrito_id):
    """Proporcionar el JSON de autoridades para elegir con un Select"""
    # Consultar
    consulta = Autoridad.query.filter_by(estatus="A").filter_by(distrito_id=distrito_id)
    # Si viene es_archivo_solicitante como parametro en el URL como true o false
    if "es_archivo_solicitante" in request.args:
        es_archivo_solicitante = request.args["es_archivo_solicitante"] == "true"
        consulta = consulta.filter_by(es_archivo_solicitante=es_archivo_solicitante)
    # Si viene es_cemasc como parametro en el URL como true o false
    if "es_cemasc" in request.args:
        es_cemasc = request.args["es_cemasc"] == "true"
        consulta = consulta.filter_by(es_cemasc=es_cemasc)
    # Si viene es_defensoria como parametro en el URL como true o false
    if "es_defensoria" in request.args:
        es_defensoria = request.args["es_defensoria"] == "true"
        consulta = consulta.filter_by(es_defensoria=es_defensoria)
    # Si viene es_extinto como parametro en el URL como true o false
    if "es_extinto" in request.args:
        es_extinto = request.args["es_extinto"] == "true"
        consulta = consulta.filter_by(es_extinto=es_extinto)
    # Si viene es_jurisdiccional como parametro en el URL como true o false
    if "es_jurisdiccional" in request.args:
        es_jurisdiccional = request.args["es_jurisdiccional"] == "true"
        consulta = consulta.filter_by(es_jurisdiccional=es_jurisdiccional)
    # Si viene es_notaria como parametro en el URL como true o false
    if "es_notaria" in request.args:
        es_notaria = request.args["es_notaria"] == "true"
        consulta = consulta.filter_by(es_notaria=es_notaria)
    # Si viene es_revisor_escrituras como parametro en el URL como true o false
    if "es_revisor_escrituras" in request.args:
        es_revisor_escrituras = request.args["es_revisor_escrituras"] == "true"
        consulta = consulta.filter_by(es_revisor_escrituras=es_revisor_escrituras)
    # Si viene es_organo_especializado como parametro en el URL como true o false
    if "es_organo_especializado" in request.args:
        es_organo_especializado = request.args["es_organo_especializado"] == "true"
        consulta = consulta.filter_by(es_organo_especializado=es_organo_especializado)
    # Ordenar
    consulta = consulta.order_by(Autoridad.descripcion_corta)
    # Elaborar datos para Select
    data = []
    for resultado in consulta.all():
        data.append(
            {
                "id": resultado.id,
                "descripcion_corta": resultado.descripcion_corta,
            }
        )
    # Entregar JSON
    return json.dumps(data)


@autoridades.route("/autoridades/select_json", methods=["GET", "POST"])
def select_autoridades_json():
    """Proporcionar el JSON de autoridades para elegir con un Select"""
    # Consultar
    consulta = Autoridad.query.filter(Autoridad.estatus == "A")
    if "es_archivo_solicitante" in request.form:
        consulta = consulta.filter_by(es_archivo_solicitante=request.form["es_archivo_solicitante"] == "true")
    if "es_extinto" in request.form:
        consulta = consulta.filter_by(es_extinto=request.form["es_extinto"] == "true")
    if "es_jurisdiccional" in request.form:
        consulta = consulta.filter_by(es_jurisdiccional=request.form["es_jurisdiccional"] == "true")
    if "clave" in request.form:
        clave = safe_clave(request.form["clave"])
        if clave != "":
            consulta = consulta.filter(Autoridad.clave.contains(clave))
    results = []
    for autoridad in consulta.order_by(Autoridad.id).limit(15).all():
        results.append(
            {
                "id": autoridad.id,
                "text": autoridad.clave + "  : " + autoridad.descripcion_corta,
            }
        )
    return {"results": results, "pagination": {"more": False}}
