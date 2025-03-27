"""
CLI Edictos
"""

from datetime import datetime

import click
import sys

from lib.exceptions import MyAnyError
from sqlalchemy import func, Integer

from portal_notarias.app import create_app
from portal_notarias.blueprints.edictos.tasks import enviar_email_acuse_recibido as enviar_email_acuse_recibido_task
from portal_notarias.blueprints.edictos.tasks import enviar_email_republicacion as enviar_email_republicacion_task
from portal_notarias.blueprints.edictos.tasks import republicacion_edictos as republicacion_edictos_task
from portal_notarias.blueprints.edictos.models import Edicto
from portal_notarias.blueprints.edictos_acuses.models import EdictoAcuse
from portal_notarias.extensions import database

app = create_app()
app.app_context().push()
database.app = app


@click.group()
def cli():
    """Edictos"""


@click.command()
@click.argument("fecha", type=str)
def republicacion_edictos(fecha: str):
    """Muestra las fechas de republicación de un edicto y permite agregar una nueva"""

    try:
        # Convertir la fecha proporcionada
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()

        # Buscar todos los edictos en 'edictos_acuses' programados para la fecha dada
        edictos_acuses = database.session.query(EdictoAcuse).filter(EdictoAcuse.fecha == fecha_dt).all()

        if not edictos_acuses:
            click.echo(f"No hay republicaciones programadas para la fecha {fecha}.")
            sys.exit(0)

        edictos_creados = []  # Lista para almacenar los IDs de los edictos insertados

        for edicto_acuse in edictos_acuses:
            edicto_id = edicto_acuse.edicto_id

            # Verificar si el edicto original existe
            edicto_original = database.session.query(Edicto).filter_by(id=edicto_id).first()
            if not edicto_original:
                click.echo(f"Advertencia: No se encontró el edicto con ID {edicto_id}. Se omite.")
                continue

            # Verificar si ya existe una republicación para esta fecha
            edicto_existente = (
                database.session.query(Edicto)
                .filter(
                    Edicto.edicto_id_original == edicto_id,
                    Edicto.fecha == fecha_dt,
                )
                .first()
            )

            if edicto_existente:
                click.echo(f"Ya existe una republicación para el edicto {edicto_id} en la fecha {fecha}. Se omite.")
                continue
            edicto_base_id = edicto_original.edicto_id_original if edicto_original.edicto_id_original else edicto_original.id
            # Si el edicto tiene un edicto_id_original, buscamos el primer edcito original
            edicto_base = database.session.query(Edicto).filter(Edicto.id == edicto_base_id).first()
            # Obtener el último número de publicación del edicto
            ultima_publicacion = (
                database.session.query(func.max(Edicto.numero_publicacion))
                .filter(Edicto.edicto_id_original == edicto_base.id)
                .scalar()
            )

            # Si no hay publicaciones previas, la primera republicación será "2"
            if ultima_publicacion is None:
                nueva_publicacion = "2"  # Primera republicación después de la original
            else:
                try:
                    nueva_publicacion = str(int(ultima_publicacion) + 1)  # convertir a int, sumar y regresar a str.
                except ValueError:
                    # Manejar el caso donde el valor no es un número válido
                    click.echo(f"Advertencia: El número de publicación '{ultima_publicacion}' no es un entero válido.")
                    nueva_publicacion = "2"  # valor por defecto el numero original

            # Crear un nuevo edicto para la republicacion
            nuevo_edicto = Edicto(
                autoridad_id=edicto_original.autoridad_id,
                fecha=fecha_dt,  # la fecha nueva de republicacion
                descripcion=edicto_original.descripcion,
                expediente=edicto_original.expediente,
                numero_publicacion=nueva_publicacion,
                archivo=edicto_original.archivo,
                url=edicto_original.url,
                acuse_num=0,
                edicto_id_original=edicto_id,  # Hace referencia al edicto original
            )

            database.session.add(nuevo_edicto)
            database.session.commit()
            edictos_creados.append(nuevo_edicto.id)  # Guardar referencia para obtener los ids después

        # Confirmar todas las inserciones de una vez
        if edictos_creados:
            # ids_creados = [str(e.id) for e in edictos_creados]
            # click.echo(f"Republicaciones creadas con IDs: {', '.join(ids_creados)}")
            mensaje = f"Republicación creada con IDs:{edictos_creados} y fecha {fecha}."
        else:
            # click.echo("No se creó ninguna republicación")
            mensaje = f"No se creó ninguna republicación para la fecha {fecha}"

    except Exception as e:
        click.echo(f"Error: {e}")
        click.echo("Error: El formato de la fecha debe ser YYYY-MM-DD.")
        sys.exit(1)

    # Memsaje de éxito
    click.echo(mensaje)


cli.add_command(republicacion_edictos)


@click.command()
@click.argument("edicto_id", type=int)
def enviar_email_acuse_recibido(edicto_id: int):
    """Enviar mensaje de acuse de recibo de un Edicto"""

    # Ejecutar tarea
    try:
        mensaje = enviar_email_acuse_recibido_task(edicto_id)
    except MyAnyError as error:
        click.echo(f"Error: {error}")
        sys.exit(1)

    # Mensaje de termino
    click.echo(mensaje)


@click.command()
@click.argument("edicto_id", type=int)
def enviar_email_republicacion(edicto_id: int):
    """Enviar mensaje de republicacion de un Edicto"""

    # Ejecutar tarea
    try:
        mensaje = enviar_email_republicacion_task(edicto_id)
    except MyAnyError as error:
        click.echo(f"Error: {error}")
        sys.exit(1)

    # Mensaje de termino
    click.echo(mensaje)


cli.add_command(enviar_email_acuse_recibido)
cli.add_command(enviar_email_republicacion)
