"""Operator forms for CRUD operations."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class OperatorForm(FlaskForm):
    """Create or edit an operator."""

    company_name = StringField(
        'Operator Name',
        validators=[
            DataRequired(message='Operator name is required.'),
            Length(max=255, message='Operator name cannot exceed 255 characters.')
        ],
        render_kw={'placeholder': 'e.g., Tennessee Valley Authority'}
    )

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=10000, message='Notes cannot exceed 10,000 characters.')],
        render_kw={'rows': 5, 'placeholder': 'Optional background or commentary'}
    )

    submit = SubmitField('Save Operator')
