"""
Edictos, formularios
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, StringField, SubmitField, RadioField
from wtforms.validators import DataRequired, Length, Optional, Regexp

from lib.safe_string import EXPEDIENTE_REGEXP, NUMERO_PUBLICACION_REGEXP


class EdictoNewForm(FlaskForm):
    """Formulario para nuevo Edicto para Notaria"""

    acuse_num = RadioField(
        "Cantidad de veces a públicar",
        coerce=int,
        choices=[("1", "1 vez"), ("2", "2 veces"), ("3", "3 veces"), ("4", "4 veces"), ("5", "5 veces")],
        validators=[DataRequired()],
    )
    fecha_acuse_1 = DateField("Publicación 1", validators=[Optional()])
    fecha_acuse_2 = DateField("Publicación 2", validators=[Optional()])
    fecha_acuse_3 = DateField("Publicación 3", validators=[Optional()])
    fecha_acuse_4 = DateField("Publicación 4", validators=[Optional()])
    fecha_acuse_5 = DateField("Publicación 5", validators=[Optional()])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    archivo = FileField("Adjuntar archivo en formato (.PDF)", validators=[Optional()])
    guardar = SubmitField("Guardar")


class EdictoNewAutoridadForm(FlaskForm):
    """Formulario para nuevo Edicto"""

    distrito = StringField("Distrito")  # Read only
    autoridad = StringField("Autoridad")  # Read only
    fecha = DateField("Fecha", validators=[DataRequired()])
    descripcion = StringField("Descripcion", validators=[DataRequired(), Length(max=256)])
    expediente = StringField("Expediente", validators=[Optional(), Length(max=16), Regexp(EXPEDIENTE_REGEXP)])
    numero_publicacion = StringField(
        "No. de publicación", validators=[Optional(), Length(max=16), Regexp(NUMERO_PUBLICACION_REGEXP)]
    )
    archivo = FileField("Archivo PDF", validators=[FileRequired()])
    guardar = SubmitField("Guardar")


class EdictoEditForm(FlaskForm):
    """Formulario EdictoEdit"""

    acuse_num = RadioField(
        "Cantidad de veces a públicar",
        coerce=int,
        choices=[("1", "1 vez"), ("2", "2 veces"), ("3", "3 veces"), ("4", "4 veces"), ("5", "5 veces")],
        validators=[DataRequired()],
    )
    fecha_acuse_1 = DateField("Publicación 1", render_kw={"readonly": True}, validators=[Optional()])  # Deshabilitado
    fecha_acuse_2 = DateField("Publicación 2", validators=[Optional()])
    fecha_acuse_3 = DateField("Publicación 3", validators=[Optional()])
    fecha_acuse_4 = DateField("Publicación 4", validators=[Optional()])
    fecha_acuse_5 = DateField("Publicación 5", validators=[Optional()])
    descripcion = StringField("Descripción", validators=[Optional(), Length(max=256)])
    guardar = SubmitField("Guardar")
