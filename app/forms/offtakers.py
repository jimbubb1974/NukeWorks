"""Forms for energy off-takers."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class OfftakerForm(FlaskForm):
    """Create or edit an off-taker."""

    organization_name = StringField(
        'Organization Name',
        validators=[DataRequired(message='Organization name is required.'), Length(max=255)],
        render_kw={'placeholder': 'e.g., Amazon, Google'}
    )

    sector = StringField(
        'Sector',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'Technology, Data Centers, Industrial, etc.'}
    )

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=10000)],
        render_kw={'rows': 4, 'placeholder': 'Optional notes about the off-taker'}
    )

    submit = SubmitField('Save Off-taker')
