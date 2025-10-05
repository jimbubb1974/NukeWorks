"""Constructor forms for CRUD operations."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class ConstructorForm(FlaskForm):
    """Create or edit a constructor."""

    company_name = StringField(
        'Constructor Name',
        validators=[
            DataRequired(message='Constructor name is required.'),
            Length(max=255, message='Constructor name cannot exceed 255 characters.')
        ],
        render_kw={'placeholder': 'e.g., Bechtel'}
    )

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=10000, message='Notes cannot exceed 10,000 characters.')],
        render_kw={'rows': 5, 'placeholder': 'Optional project history or key details'}
    )

    submit = SubmitField('Save Constructor')
