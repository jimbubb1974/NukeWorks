"""Forms for managing company records."""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class CompanyForm(FlaskForm):
    """Create or update a company record."""

    company_name = StringField(
        'Company Name',
        validators=[DataRequired(message='Company name is required'), Length(max=255)]
    )

    company_type = StringField(
        'Company Type',
        validators=[Optional(), Length(max=100)]
    )

    sector = StringField(
        'Sector',
        validators=[Optional(), Length(max=100)]
    )

    website = StringField(
        'Website',
        validators=[Optional(), Length(max=255)]
    )

    headquarters_country = StringField(
        'Headquarters Country',
        validators=[Optional(), Length(max=100)]
    )

    headquarters_region = StringField(
        'Headquarters Region',
        validators=[Optional(), Length(max=100)]
    )

    is_mpr_client = BooleanField('MPR Client')
    is_internal = BooleanField('Internal Company')

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=5000)],
        render_kw={'rows': 4}
    )

    submit = SubmitField('Save')
