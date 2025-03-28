"""
Edictos, formularios
"""

from flask_wtf import FlaskForm
from wtforms import DateField, FileField, StringField, SubmitField, RadioField
from wtforms.validators import DataRequired, Length, Optional


class EdictoNewForm(FlaskForm):
    """Formulario para nuevo Edicto para Notaria"""

    acuse_num = RadioField(
        "Cantidad de veces a publicar",
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
    distrito = StringField("Distrito")  # Read only
    autoridad = StringField("Autoridad")  # Read only
    archivo = FileField("Adjuntar archivo en formato (.PDF)", validators=[Optional()])
    guardar = SubmitField("Guardar")


class EdictoEditForm(FlaskForm):
    """Formulario EdictoEdit"""

    distrito = StringField("Distrito")  # Read only
    autoridad = StringField("Autoridad")  # Read only
    fecha_acuse_1 = DateField("Publicación 1", render_kw={"readonly": True}, validators=[Optional()])  # Deshabilitado
    fecha_acuse_2 = DateField("Publicación 2", validators=[Optional()])
    fecha_acuse_3 = DateField("Publicación 3", validators=[Optional()])
    fecha_acuse_4 = DateField("Publicación 4", validators=[Optional()])
    fecha_acuse_5 = DateField("Publicación 5", validators=[Optional()])
    descripcion = StringField("Descripción", validators=[Optional(), Length(max=256)])
    guardar = SubmitField("Guardar")
