"""Forms for managing company records."""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, TextAreaField, SubmitField, DateField
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

    website = StringField(
        'Website',
        validators=[Optional(), Length(max=255)]
    )

    headquarters_country = StringField(
        'Headquarters Country',
        validators=[Optional(), Length(max=100)]
    )

    is_mpr_client = BooleanField('MPR Client')
    is_internal = BooleanField('Internal Company')

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=5000)],
        render_kw={'rows': 4}
    )

    # MPR Client CRM Fields (shown only when is_mpr_client is True)
    client_priority = SelectField(
        'Client Priority',
        choices=[
            ('', '-- Select Priority --'),
            ('High', 'High'),
            ('Medium', 'Medium'),
            ('Low', 'Low'),
        ],
        validators=[Optional()]
    )

    client_tier = SelectField(
        'Client Tier',
        choices=[
            ('', '-- Select Tier --'),
            ('Tier 1', 'Tier 1'),
            ('Tier 2', 'Tier 2'),
            ('Tier 3', 'Tier 3'),
            ('Tier 4', 'Tier 4'),
        ],
        validators=[Optional()]
    )

    client_status = SelectField(
        'Client Status',
        choices=[
            ('', '-- Select Status --'),
            ('Active', 'Active'),
            ('Warm', 'Warm'),
            ('Cold', 'Cold'),
            ('Prospective', 'Prospective')
        ],
        validators=[Optional()]
    )

    relationship_notes = TextAreaField(
        'Relationship Notes',
        validators=[Optional(), Length(max=2000)],
        render_kw={'rows': 3, 'placeholder': 'Internal strategy notes and relationship insights'}
    )

    submit = SubmitField('Save')


class CompanyPersonnelRelationshipForm(FlaskForm):
    """Add a relationship between a client contact and an MPR person."""

    external_personnel_id = SelectField(
        'Client Contact',
        coerce=int,
        choices=[],
        validators=[DataRequired(message='Select a client contact')]
    )

    internal_personnel_id = SelectField(
        'MPR Person',
        coerce=int,
        choices=[],
        validators=[DataRequired(message='Select an MPR person')]
    )

    relationship_type = SelectField(
        'Relationship Type',
        choices=[
            ('Primary Contact', 'Primary Contact'),
            ('Technical Contact', 'Technical Contact'),
            ('Business Contact', 'Business Contact'),
            ('Account Manager', 'Account Manager'),
            ('Other', 'Other'),
        ],
        validators=[Optional()]
    )

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=1000)],
        render_kw={'rows': 2}
    )

    submit = SubmitField('Add')
