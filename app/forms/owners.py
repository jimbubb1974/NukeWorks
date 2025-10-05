"""Forms for owner/developer CRUD operations."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional

OWNER_TYPES = [
    ('IOU', 'Investor-Owned Utility'),
    ('COOP', 'Cooperative'),
    ('Public Power', 'Public Power'),
    ('IPP', 'Independent Power Producer'),
    ('Municipal', 'Municipal Utility'),
    ('Other', 'Other')
]

ENGAGEMENT_LEVELS = [
    ('Intrigued', 'Intrigued'),
    ('Interested', 'Interested'),
    ('Invested', 'Invested'),
    ('Inservice', 'Inservice'),
]

CLIENT_STATUS_CHOICES = [
    ('Active', 'Active'),
    ('Warm', 'Warm'),
    ('Cold', 'Cold'),
    ('Prospective', 'Prospective'),
]

CLIENT_PRIORITY_CHOICES = [
    ('High', 'High'),
    ('Medium', 'Medium'),
    ('Low', 'Low'),
    ('Strategic', 'Strategic'),
    ('Opportunistic', 'Opportunistic'),
]


class OwnerDeveloperForm(FlaskForm):
    """Form for creating or editing an owner/developer."""

    company_name = StringField(
        'Company Name',
        validators=[DataRequired(message='Company name is required.'), Length(max=255)],
        render_kw={'placeholder': 'e.g., Tennessee Valley Authority'}
    )

    company_type = SelectField(
        'Company Type',
        choices=[('', '-- Select Type --')] + OWNER_TYPES,
        validators=[Optional()],
        coerce=str
    )

    engagement_level = SelectField(
        'Engagement Level',
        choices=[('', '-- Select Engagement --')] + ENGAGEMENT_LEVELS,
        validators=[Optional()],
        coerce=str
    )

    client_status = SelectField(
        'Client Status',
        choices=[('', '-- Select Status --')] + CLIENT_STATUS_CHOICES,
        validators=[Optional()],
        coerce=str
    )

    client_priority = SelectField(
        'Client Priority',
        choices=[('', '-- Select Priority --')] + CLIENT_PRIORITY_CHOICES,
        validators=[Optional()],
        coerce=str
    )

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=10000)],
        render_kw={'rows': 4, 'placeholder': 'Optional notes or relationship summary'}
    )

    submit = SubmitField('Save Owner')
