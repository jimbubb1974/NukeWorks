"""Forms for the research workflow."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, IntegerField, RadioField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length


class ExportForm(FlaskForm):
    scope = RadioField(
        'Scope',
        choices=[('all', 'All entities'), ('selected', 'Selected companies')],
        default='all',
    )
    chunk_size = IntegerField(
        'Companies per chunk',
        default=20,
        validators=[NumberRange(min=5, max=100)],
    )
    submit = SubmitField('Generate Export Package')


class ImportForm(FlaskForm):
    run_name = StringField(
        'Research Run Name',
        validators=[DataRequired(), Length(max=200)],
        render_kw={'placeholder': 'e.g. April 2026 Quarterly Research'},
    )
    response_file = FileField(
        'AI Response File(s)',
        validators=[
            FileRequired(),
            FileAllowed(['json'], 'JSON files only'),
        ],
    )
    submit = SubmitField('Import & Stage for Review')
