"""
Edictos, vistas
"""

from datetime import datetime, date, time, timedelta
import json
from urllib.parse import quote

from flask import Blueprint, current_app, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from pytz import timezone
from werkzeug.datastructures import CombinedMultiDict
from werkzeug.exceptions import NotFound

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.exceptions import (
    MyBucketNotFoundError,
    MyFileNotFoundError,
    MyNotValidParamError,
)
from lib.exceptions import MyAnyError
from lib.google_cloud_storage import get_blob_name_from_url, get_media_type_from_filename, get_file_from_gcs
from lib.safe_string import safe_expediente, safe_message, safe_numero_publicacion, safe_string
from lib.storage import GoogleCloudStorage, NotAllowedExtesionError, NotConfiguredError, UnknownExtesionError
from lib.time_to_text import dia_mes_ano
from portal_notarias.blueprints.usuarios.decorators import permission_required

from portal_notarias.blueprints.autoridades.models import Autoridad
from portal_notarias.blueprints.bitacoras.models import Bitacora
from portal_notarias.blueprints.distritos.models import Distrito
from portal_notarias.blueprints.modulos.models import Modulo
from portal_notarias.blueprints.permisos.models import Permiso
from portal_notarias.blueprints.edictos.models import Edicto
from portal_notarias.blueprints.edictos.forms import EdictoNewForm, EdictoNewAutoridadForm, EdictoEditForm
from portal_notarias.blueprints.edictos_acuses.models import EdictoAcuse


# Zona horaria
TIMEZONE = "America/Mexico_City"
local_tz = timezone(TIMEZONE)
medianoche = time.min

MODULO = "EDICTOS"

LIMITE_DIAS = 365  # Un anio
LIMITE_ADMINISTRADORES_DIAS = 3650  # Administradores pueden manipular diez anios
LIMITE_DIAS_ELIMINAR = LIMITE_DIAS_RECUPERAR = LIMITE_DIAS_EDITAR = 1

edictos = Blueprint("edictos", __name__, template_folder="templates")


@edictos.route("/edictos/acuses/<id_hashed>")
def checkout(id_hashed):
    """Acuse del Edicto"""
    edicto = Edicto.query.get_or_404(Edicto.decode_id(id_hashed))
    dia, mes, anio = dia_mes_ano(edicto.creado)
    return render_template(
        "edictos/print.jinja2",
        edicto=edicto,
        dia=dia,
        mes=mes.upper(),
        anio=anio,
        fecha_del_acuse=None,
    )


@edictos.route("/edictos/acuses/<id_hashed>/<edicto_acuse_id>")
def checkout_notaria(id_hashed, edicto_acuse_id):
    """Acuse de las republicaciones del Edicto para notarias"""
    edicto = Edicto.query.get_or_404(Edicto.decode_id(id_hashed))
    edicto_acuse = EdictoAcuse.query.get_or_404(edicto_acuse_id)
    dia, mes, anio = dia_mes_ano(edicto.creado)
    fecha_del_acuse = edicto_acuse.fecha
    return render_template(
        "edictos/print.jinja2",
        edicto=edicto,
        dia=dia,
        mes=mes.upper(),
        anio=anio,
        fecha_del_acuse=fecha_del_acuse,
    )


@edictos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@edictos.route("/edictos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Edictos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Edicto.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "autoridad_id" in request.form:
        autoridad = Autoridad.query.get(request.form["autoridad_id"])
        if autoridad:
            consulta = consulta.filter_by(autoridad=autoridad)
    if "fecha_desde" in request.form:
        consulta = consulta.filter(Edicto.fecha >= request.form["fecha_desde"])
    if "fecha_hasta" in request.form:
        consulta = consulta.filter(Edicto.fecha <= request.form["fecha_hasta"])
    if "descripcion" in request.form:
        consulta = consulta.filter(Edicto.descripcion.contains(safe_string(request.form["descripcion"])))
    if "numero_publicacion" in request.form:
        consulta = consulta.filter(Edicto.numero_publicacion.contains(request.form["numero_publicacion"]))
    # Ordenar y paginar
    registros = consulta.order_by(Edicto.fecha.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        # Crear un diccionario para almacenar el detalle
        detalle = {
            "descripcion": resultado.descripcion,
        }
        # Verificar si 'edicto_id_original' es igual a 0
        if resultado.edicto_id_original == 0:
            # Si es igual a 0, agregar la URL al diccionario
            detalle["url"] = url_for("edictos.detail", edicto_id=resultado.id)
        data.append(
            {
                "fecha": resultado.fecha.strftime("%Y-%m-%d %H:%M:%S"),
                "detalle": detalle,
                "expediente": resultado.expediente,
                "numero_publicacion": resultado.numero_publicacion,
                "archivo": {
                    "descargar_url": resultado.descargar_url,
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@edictos.route("/edictos/datatable_json_admin", methods=["GET", "POST"])
def datatable_json_admin():
    """DataTable JSON para listado de edictos administradores"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Edicto.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "autoridad_id" in request.form:
        autoridad = Autoridad.query.get(request.form["autoridad_id"])
        if autoridad:
            consulta = consulta.filter_by(autoridad=autoridad)
    if "fecha_desde" in request.form:
        consulta = consulta.filter(Edicto.fecha >= request.form["fecha_desde"])
    if "fecha_hasta" in request.form:
        consulta = consulta.filter(Edicto.fecha <= request.form["fecha_hasta"])
    if "descripcion" in request.form:
        consulta = consulta.filter(Edicto.descripcion.like("%" + safe_string(request.form["descripcion"]) + "%"))
    if "expediente" in request.form:
        try:
            expediente = safe_expediente(request.form["expediente"])
            consulta = consulta.filter_by(expediente=expediente)
        except (IndexError, ValueError):
            pass
    if "numero_publicacion" in request.form:
        consulta = consulta.filter(Edicto.numero_publicacion.contains(request.form["numero_publicacion"]))
    registros = consulta.order_by(Edicto.fecha.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for edicto in registros:
        data.append(
            {
                "creado": edicto.creado.strftime("%Y-%m-%d %H:%M:%S"),
                "autoridad": edicto.autoridad.clave,
                "fecha": edicto.fecha.strftime("%Y-%m-%d %H:%M:%S"),
                "detalle": {
                    "descripcion": edicto.descripcion,
                    "url": url_for("edictos.detail", edicto_id=edicto.id),
                },
                "expediente": edicto.expediente,
                "numero_publicacion": edicto.numero_publicacion,
                "archivo": {
                    "descargar_url": url_for("edictos.download", url=quote(edicto.url)),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@edictos.route("/edictos")
def list_active():
    """Listado de Edictos activos"""
    # Si es administrador ve todo
    if current_user.can_admin("EDICTOS"):
        return render_template(
            "edictos/list_admin.jinja2",
            autoridad=None,
            filtros=json.dumps({"estatus": "A"}),
            titulo="Todos los Edictos",
            estatus="A",
        )
    # Si es notaria ve lo de su autoridad
    if current_user.autoridad.es_notaria:
        autoridad = current_user.autoridad
        return render_template(
            "edictos/list.jinja2",
            autoridad=autoridad,
            filtros=json.dumps({"autoridad_id": autoridad.id, "estatus": "A"}),
            titulo=f"Edictos de {autoridad.distrito.nombre_corto}, {autoridad.descripcion_corta}",
            estatus="A",
        )
    # Ninguno de los anteriores
    return redirect(url_for("edictos.list_distritos"))


@edictos.route("/edictos/distrito/<int:distrito_id>")
def list_autoridades(distrito_id):
    """Listado de Autoridades de un distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    return render_template(
        "edictos/list_autoridades.jinja2",
        distrito=distrito,
        autoridades=Autoridad.query.filter_by(distrito=distrito)
        .filter_by(es_jurisdiccional=True)
        .filter_by(estatus="A")
        .order_by(Autoridad.clave)
        .all(),
    )


@edictos.route("/edictos/autoridad/<int:autoridad_id>")
def list_autoridad_edictos(autoridad_id):
    """Listado de Edictos activos de una autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    if current_user.can_admin("EDICTOS"):
        plantilla = "edictos/list_admin.jinja2"
    else:
        plantilla = "edictos/list.jinja2"
    return render_template(
        plantilla,
        autoridad=autoridad,
        filtros=json.dumps({"autoridad_id": autoridad.id, "estatus": "A"}),
        titulo=f"Edictos de {autoridad.distrito.nombre_corto}, {autoridad.descripcion_corta}",
        estatus="A",
    )


@edictos.route("/edictos/distritos")
def list_distritos():
    """Listado de Distritos"""
    return render_template(
        "edictos/list_distritos.jinja2",
        distritos=Distrito.query.filter_by(es_distrito_judicial=True).filter_by(estatus="A").order_by(Distrito.nombre).all(),
    )


@edictos.route("/edictos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Edictos inactivos"""
    return render_template(
        "edictos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Edictos inactivos",
        estatus="B",
    )


@edictos.route("/edictos/inactivos/autoridad/<int:autoridad_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_autoridad_edictos_inactive(autoridad_id):
    """Listado de Edictos inactivos de una autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    if current_user.can_admin("EDICTOS"):
        plantilla = "edictos/list_admin.jinja2"
    else:
        plantilla = "edictos/list.jinja2"
    return render_template(
        plantilla,
        autoridad=autoridad,
        filtros=json.dumps({"autoridad_id": autoridad.id, "estatus": "B"}),
        titulo=f"Edictos inactivos de {autoridad.distrito.nombre_corto}, {autoridad.descripcion_corta}",
        estatus="B",
    )


@edictos.route("/edictos/descargar", methods=["GET"])
@permission_required(MODULO, Permiso.ADMINISTRAR)
def download():
    """Descargar archivo desde Google Cloud Storage"""
    url = request.args.get("url")
    try:
        # Obtener nombre del blob
        blob_name = get_blob_name_from_url(url)
        # Obtener tipo de media
        media_type = get_media_type_from_filename(blob_name)
        # Obtener archivo
        archivo = get_file_from_gcs(current_app.config["CLOUD_STORAGE_DEPOSITO_EDICTOS"], blob_name)
    except MyAnyError as error:
        flash(str(error), "warning")
        return redirect(url_for("edictos.list_active"))
    # Entregar archivo
    return current_app.response_class(archivo, mimetype=media_type)


@edictos.route("/edictos/<int:edicto_id>")
def detail(edicto_id):
    """Detalle de un Edicto"""
    edicto = Edicto.query.get_or_404(edicto_id)
    return render_template("edictos/detail.jinja2", edicto=edicto)


def new_success(edicto):
    """Mensaje de éxito en nuevo edicto"""
    piezas = ["Nuevo edicto"]
    if edicto.expediente != "":
        piezas.append(f"expediente {edicto.expediente},")
    if edicto.numero_publicacion != "":
        piezas.append(f"número {edicto.numero_publicacion},")
    piezas.append(f"fecha {edicto.fecha.strftime('%Y-%m-%d')} de {edicto.autoridad.clave}")
    bitacora = Bitacora(
        modulo=Modulo.query.filter_by(nombre=MODULO).first(),
        usuario=current_user,
        descripcion=safe_message(" ".join(piezas)),
        url=url_for("edictos.detail", edicto_id=edicto.id),
    )
    bitacora.save()
    return bitacora


def new_notaria_success(edicto):
    """Mensaje de éxito en nuevo edicto"""
    piezas = ["Nuevo edicto"]
    piezas.append(f"fecha {edicto.fecha.strftime('%Y-%m-%d')} de {edicto.autoridad.clave}")
    bitacora = Bitacora(
        modulo=Modulo.query.filter_by(nombre=MODULO).first(),
        usuario=current_user,
        descripcion=safe_message(" ".join(piezas)),
        url=url_for("edictos.detail", edicto_id=edicto.id),
    )
    bitacora.save()
    return bitacora


@edictos.route("/edictos/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Subir Edicto para una notaria"""
    # Definir la fecha del edicto, simpre es HOY, se usa para GCS
    hoy_date = datetime.today().date()

    # Validar autoridad
    autoridad = current_user.autoridad
    if autoridad.estatus != "A":
        flash("La Notaria no es activa.", "warning")
        return redirect(url_for("edictos.list_active"))
    if not autoridad.distrito.es_distrito_judicial:
        flash("El Distrito no es jurisdiccional.", "warning")
        return redirect(url_for("edictos.list_active"))
    if not autoridad.es_notaria:
        flash("La Notarias no tiene en verdadero el boleano que lo define como notaria.", "warning")
        return redirect(url_for("edictos.list_active"))
    if autoridad.directorio_edictos is None or autoridad.directorio_edictos == "":
        flash("La Notaria no tiene directorio para edictos.", "warning")
        return redirect(url_for("edictos.list_active"))

    # Si viene el formulario
    form = EdictoNewForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():
        es_valido = True

        # Validar la descripcion
        descripcion = safe_string(form.descripcion.data, max_len=64, save_enie=True)
        if descripcion == "":
            flash("La descripción es incorrecta.", "warning")
            es_valido = False

        # Validad que acuse_num se entero
        try:
            acuse_num = int(form.acuse_num.data)
        except ValueError:
            flash("Especificar una cantidad publicaciones válida.", "warning")
            es_valido = False

        # Validar que el acuse_num sea entre 1 y 5
        if not 1 <= acuse_num <= 5:
            flash("Especificar una cantidad de publicaciones entre 1 y 5.", "warning")
            es_valido = False

        # Si el usuario seleccionó la opcion de 1 en el radiobutton
        if acuse_num == 1:
            # Establecer la fecha de hoy en el primer campo de fecha
            form.fecha_acuse_1.data = hoy_date.strftime("%Y-%m-%d")

        # Validar las fechas de los acuses que se ingresan manualmente por el usuario
        limite_futuro_date = hoy_date + timedelta(days=30)
        fechas_acuses_list = []
        for i in range(1, acuse_num + 1):
            # Asegura de que 'i' esté correctamente definido dentro del bucle 'for'
            fecha_acuse_str = getattr(form, f"fecha_acuse_{i}").data
            # Verifica si fecha_acuse_str es None y maneja el caso adecuadamente
            if fecha_acuse_str is None:
                # Asignar la fecha actual como valor predeterminado
                fecha_acuse_str = hoy_date.strftime("%Y-%m-%d")
            # Asegura que la fecha_acuse_str sea una cadena de texto antes de pasarla a strptime()
            if isinstance(fecha_acuse_str, date):
                # Si ya es un objeto de fecha, no necesitas convertirlo
                fecha_acuse = fecha_acuse_str
            else:
                # Convierte la cadena de texto a un objeto de fecha
                fecha_acuse = datetime.strptime(fecha_acuse_str, "%Y-%m-%d").date()
            # Agrega la variable fecha_acuse a la lista fechas_acuses_list.
            fechas_acuses_list.append(fecha_acuse)

        for fecha_acuse in fechas_acuses_list:
            if fecha_acuse is None:  # Validar que NO sea nulo
                flash("Falta una de las fechas de publicación.", "warning")
                es_valido = False
                break
            if fecha_acuse < hoy_date:  # Validar que NO sea del pasado
                flash("La fecha de publicación no puede ser del pasado.", "warning")
                es_valido = False
                break
            if fecha_acuse > limite_futuro_date:  # Validar que NO sea posterior al limite permitido
                flash("Solo se permiten fechas de publicación hasta un mes en el futuro.", "warning")
                es_valido = False

        # Inicializar la liberia Google Cloud Storage con el directorio base, la fecha, las extensiones permitidas y los meses como palabras
        gcstorage = GoogleCloudStorage(
            base_directory=autoridad.directorio_edictos,
            upload_date=hoy_date,
            allowed_extensions=["pdf"],
            month_in_word=True,
            bucket_name=current_app.config["CLOUD_STORAGE_DEPOSITO_EDICTOS"],
        )

        # Validar archivo
        archivo = request.files["archivo"]
        try:
            gcstorage.set_content_type(archivo.filename)
        except (NotAllowedExtesionError, UnknownExtesionError):
            flash("Tipo de archivo no permitido o desconocido.", "warning")
            es_valido = False

        # Si NO es válido, entonces se vuelve a mostrar el formulario
        if es_valido is False:
            return render_template("edictos/new.jinja2", form=form)

        # Insertar el registro en la base de datos
        edicto = Edicto(
            autoridad=autoridad,
            fecha=hoy_date,
            acuse_num=acuse_num,
            descripcion=descripcion,
            numero_publicacion="1",  # Primera publicación siempre es "1"
        )
        edicto.save()

        # Insertar los acuses solo si la validación es exitosa
        for fecha_acuse in fechas_acuses_list:

            # Verificar que la fecha del acuse no sea la fecha de hoy
            if fecha_acuse != hoy_date:
                acuse = EdictoAcuse(
                    edicto_id=edicto.id,
                    fecha=fecha_acuse,
                )
                acuse.save()

        # Subir a Google Cloud Storage
        es_exitoso = True
        try:
            gcstorage.set_filename(hashed_id=edicto.encode_id(), description=descripcion)
            gcstorage.upload(archivo.stream.read())
        except (NotAllowedExtesionError, UnknownExtesionError):
            flash("Tipo de archivo no permitido o desconocido.", "warning")
            es_exitoso = False
        except NotConfiguredError:
            flash("Error al subir el archivo porque falla la configuración de GCS.", "danger")
            es_exitoso = False
        except Exception as error:
            flash(f"Error inesperado: {str(error)}", "danger")
            es_exitoso = False

        # Si se sube con exito, actualizar el registro del edicto con el archivo y la URL y mostrar el detalle
        if es_exitoso:
            edicto.archivo = gcstorage.filename
            edicto.url = gcstorage.url
            edicto.save()
            bitacora = new_notaria_success(edicto)
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)

        # Como no se subio con exito, se cambia el estatus a "B"
        edicto.estatus = "B"
        edicto.save()

    # Prellenado de los campos
    hoy_date = datetime.today().date()
    for i in range(1, 6):
        setattr(form, f"fecha_acuse_{i}", hoy_date.strftime("%Y-%m-%d"))
    return render_template("edictos/new.jinja2", form=form)


@edictos.route("/edictos/nuevo/<int:autoridad_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.ADMINISTRAR)
def new_for_autoridad(autoridad_id):
    """Subir Edicto para una autoridad dada"""

    # Para validar la fecha
    hoy = datetime.date.today()
    hoy_dt = datetime.datetime(year=hoy.year, month=hoy.month, day=hoy.day)
    limite_dt = hoy_dt + datetime.timedelta(days=-LIMITE_ADMINISTRADORES_DIAS)

    # Validar autoridad
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    if autoridad is None:
        flash("El juzgado/autoridad no existe.", "warning")
        return redirect(url_for("edictos.list_active"))
    if autoridad.estatus != "A":
        flash("El juzgado/autoridad no es activa.", "warning")
        return redirect(url_for("autoridades.detail", autoridad_id=autoridad.id))
    if not autoridad.distrito.es_distrito_judicial:
        flash("El juzgado/autoridad no está en un distrito jurisdiccional.", "warning")
        return redirect(url_for("autoridades.detail", autoridad_id=autoridad.id))
    if not autoridad.es_jurisdiccional:
        flash("El juzgado/autoridad no es jurisdiccional.", "warning")
        return redirect(url_for("autoridades.detail", autoridad_id=autoridad.id))
    if autoridad.directorio_edictos is None or autoridad.directorio_edictos == "":
        flash("El juzgado/autoridad no tiene directorio para edictos.", "warning")
        return redirect(url_for("autoridades.detail", autoridad_id=autoridad.id))

    # Si viene el formulario
    form = EdictoNewAutoridadForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():
        es_valido = True

        # Validar fecha
        fecha = form.fecha.data
        if not limite_dt <= datetime.datetime(year=fecha.year, month=fecha.month, day=fecha.day) <= hoy_dt:
            flash(f"La fecha no debe ser del futuro ni anterior a {LIMITE_ADMINISTRADORES_DIAS} días.", "warning")
            form.fecha.data = hoy
            es_valido = False

        # Validar descripcion
        descripcion = safe_string(form.descripcion.data)
        if descripcion == "":
            flash("La descripción es incorrecta.", "warning")
            es_valido = False

        # Validar expediente
        try:
            expediente = safe_expediente(form.expediente.data)
        except (IndexError, ValueError):
            flash("El expediente es incorrecto.", "warning")
            es_valido = False

        # Validar número de publicación
        try:
            numero_publicacion = safe_numero_publicacion(form.numero_publicacion.data)
        except (IndexError, ValueError):
            flash("El número de publicación es incorrecto.", "warning")
            es_valido = False

        # Inicializar la liberia Google Cloud Storage con el directorio base, la fecha, las extensiones permitidas y los meses como palabras
        gcstorage = GoogleCloudStorage(
            base_directory=autoridad.directorio_edictos,
            upload_date=fecha,
            allowed_extensions=["pdf"],
            month_in_word=True,
            bucket_name=current_app.config["CLOUD_STORAGE_DEPOSITO_EDICTOS"],
        )

        # Validar archivo
        archivo = request.files["archivo"]
        try:
            gcstorage.set_content_type(archivo.filename)
        except (NotAllowedExtesionError, UnknownExtesionError):
            flash("Tipo de archivo no permitido o desconocido.", "warning")
            es_valido = False

        # No es válido, entonces se vuelve a mostrar el formulario
        if es_valido is False:
            return render_template("edictos/new_for_autoridad.jinja2", form=form, autoridad=autoridad)

        # Insertar registro
        edicto = Edicto(
            autoridad=autoridad,
            fecha=fecha,
            descripcion=descripcion,
            expediente=expediente,
            numero_publicacion=numero_publicacion,
        )
        edicto.save()

        # Subir a Google Cloud Storage
        es_exitoso = True
        try:
            gcstorage.set_filename(hashed_id=edicto.encode_id(), description=descripcion)
            gcstorage.upload(archivo.stream.read())
        except (NotAllowedExtesionError, UnknownExtesionError):
            flash("Tipo de archivo no permitido o desconocido.", "warning")
            es_exitoso = False
        except NotConfiguredError:
            flash("Error al subir el archivo porque falla la configuración de GCS.", "danger")
            es_exitoso = False
        except Exception:
            flash("Error desconocido al subir el archivo.", "danger")
            es_exitoso = False

        # Si se sube con exito, actualizar el registro con la URL del archivo y mostrar el detalle
        if es_exitoso:
            edicto.archivo = gcstorage.filename
            edicto.url = gcstorage.url
            edicto.save()
            bitacora = new_success(edicto)
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)

    # Prellenado de los campos
    form.distrito.data = autoridad.distrito.nombre
    form.autoridad.data = autoridad.descripcion
    form.fecha.data = hoy
    return render_template("edictos/new_for_autoridad.jinja2", form=form, autoridad=autoridad)


@edictos.route("/edictos/edicion/<int:edicto_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(edicto_id):
    """Editar Edicto"""
    edicto = Edicto.query.get_or_404(edicto_id)

    # Validar autoridad
    autoridad = edicto.autoridad
    if autoridad.estatus != "A":
        flash("La Notaría no esta activa.", "warning")
        return redirect(url_for("edictos.list_active"))
    if not autoridad.distrito.es_distrito_judicial:
        flash("El Distrito no es jurisdiccional.", "warning")
        return redirect(url_for("edictos.list_active"))
    if not autoridad.es_notaria:
        flash("La Notaria no tiene en verdadero el boleano que la define como notaria.", "warning")
        return redirect(url_for("edictos.list_active"))
    if autoridad.directorio_edictos is None or autoridad.directorio_edictos == "":
        flash("La Notaria no tiene directorio para edictos.", "warning")
        return redirect(url_for("edictos.list_active"))

    # Si NO es administrador
    if not (current_user.can_admin(MODULO)):
        # Validar que le pertenezca
        if current_user.autoridad_id != edicto.autoridad_id:
            flash("No puede editar registros ajenos.", "warning")
            return redirect(url_for("edictos.list_active"))
        # Asegurar que edicto.creado tenga zona horaria
        if edicto.creado.tzinfo is None:
            edicto_creado = local_tz.localize(edicto.creado)  # Agregar la zona horaria si no la tiene
        else:
            edicto_creado = edicto.creado.astimezone(local_tz)  # Convertir a la zona horaria local si ya tiene una zona horaria
        # Si fue creado hace más de LIMITE_DIAS_EDITAR
        if edicto_creado < datetime.now(local_tz) - timedelta(days=LIMITE_DIAS_EDITAR):
            flash(f"Ya no puede editar porque fue creado hace más de {LIMITE_DIAS_EDITAR} día.", "warning")
            return redirect(url_for("edictos.detail", edicto_id=edicto.id))

    # Obtener los acuses asociados al edicto
    acuses = EdictoAcuse.query.filter_by(edicto_id=edicto.id).order_by(EdictoAcuse.fecha).all()

    # Si viene el formulario
    form = EdictoEditForm()
    if form.validate_on_submit():
        es_valido = True

        # Validar la descripción
        descripcion = safe_string(form.descripcion.data, save_enie=True)
        if descripcion == "":
            flash("La descripción es incorrecta.", "warning")
            es_valido = False

        # Guardar cambios en el edicto
        edicto.descripcion = descripcion
        edicto.save()

        # Actualizar los acuses
        for i, acuse in enumerate(acuses):
            if i + 2 <= 5:
                fecha_acuse_field = getattr(form, f"fecha_acuse_{i + 2}")
                fecha_acuse = fecha_acuse_field.data
                if fecha_acuse is None:
                    flash("Falta una de las fechas de publicación.", "warning")
                    es_valido = False
                    break
                if fecha_acuse < datetime.today().date():
                    flash("La fecha de publicación no puede ser del pasado.", "warning")
                    es_valido = False
                    break
                acuse.fecha = fecha_acuse
                acuse.save()

        if not es_valido:
            return render_template("edictos/edit.jinja2", form=form, edicto=edicto)
        # Registrar en la bitácora
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Edicto {edicto.descripcion} actualizado."),
            url=url_for("edictos.detail", edicto_id=edicto.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)

    # Pre-llenar el formulario con los datos del edicto y los acuses
    form.descripcion.data = edicto.descripcion
    for i, acuse in enumerate(acuses):
        if i + 2 <= 5:  # Asegurarse de que no exceda el número de campos de fecha en el formulario
            fecha_acuse_field = getattr(form, f"fecha_acuse_{i + 2}")
            fecha_acuse_field.data = acuse.fecha
    return render_template("edictos/edit.jinja2", form=form, edicto=edicto)


@edictos.route("/edictos/ver_archivo_pdf/<int:edicto_id>")
def view_file_pdf(edicto_id):
    """Ver archivo PDF de Edicto para insertarlo en un iframe en el detalle"""

    # Consultar
    edicto = Edicto.query.get_or_404(edicto_id)

    # Obtener el contenido del archivo
    try:
        archivo = get_file_from_gcs(
            bucket_name=current_app.config["CLOUD_STORAGE_DEPOSITO_EDICTOS"],
            blob_name=get_blob_name_from_url(edicto.url),
        )
    except (MyBucketNotFoundError, MyFileNotFoundError, MyNotValidParamError) as error:
        raise NotFound("No se encontró el archivo.") from error

    # Entregar el archivo
    response = make_response(archivo)
    response.headers["Content-Type"] = "application/pdf"
    return response
