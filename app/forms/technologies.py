"""Forms for managing technology products."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, FloatField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class TechnologyForm(FlaskForm):
    """Create or edit a technology product."""

    product_name = StringField(
        'Model',
        validators=[DataRequired(message='Model name is required.'), Length(max=255)],
        render_kw={'placeholder': 'e.g., AP1000, eVinci'}
    )

    vendor_id = SelectField(
        'Vendor',
        coerce=int,
        validators=[DataRequired(message='Select a vendor.')]
    )

    reactor_type = StringField(
        'Reactor Type',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'PWR, SFR, Heat Pipe, etc.'}
    )

    generation = StringField(
        'Generation',
        validators=[Optional(), Length(max=50)],
        render_kw={'placeholder': 'III+, IV'}
    )

    gross_capacity_mwt = FloatField(
        'Gross Capacity (MWt)',
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'placeholder': 'e.g., 345'}
    )

    thermal_efficiency = FloatField(
        'Efficiency (%)',
        validators=[Optional(), NumberRange(min=0, max=100)],
        render_kw={'placeholder': 'e.g., 34'}
    )

    fuel_type = StringField(
        'Fuel Type',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'e.g., HALEU, TRISO'}
    )

    fuel_enrichment = StringField(
        'Fuel Enrichment Level',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'e.g., 5% U-235'}
    )

    design_status = StringField(
        'Status of Design',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'Conceptual, Licensed, Operating'}
    )

    mpr_project_ids = StringField(
        'MPR Project IDs',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'Comma-separated IDs'}
    )

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=10000)],
        render_kw={'rows': 4, 'placeholder': 'Additional technical notes'}
    )

    submit = SubmitField('Save Technology')
