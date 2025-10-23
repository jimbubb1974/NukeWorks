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
            ('Strategic', 'Strategic'),
            ('High', 'High'),
            ('Medium', 'Medium'),
            ('Low', 'Low'),
            ('Opportunistic', 'Opportunistic')
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

    relationship_strength = SelectField(
        'Relationship Strength',
        choices=[
            ('', '-- Select Strength --'),
            ('Strong', 'Strong'),
            ('Good', 'Good'),
            ('Needs Attention', 'Needs Attention'),
            ('At Risk', 'At Risk'),
            ('New', 'New')
        ],
        validators=[Optional()]
    )

    relationship_notes = TextAreaField(
        'Relationship Notes',
        validators=[Optional(), Length(max=2000)],
        render_kw={'rows': 3, 'placeholder': 'Internal strategy notes and relationship insights'}
    )

    last_contact_date = DateField(
        'Last Contact Date',
        validators=[Optional()]
    )

    last_contact_type = SelectField(
        'Last Contact Type',
        choices=[
            ('', '-- Select Type --'),
            ('In-person', 'In-person'),
            ('Phone', 'Phone'),
            ('Email', 'Email'),
            ('Video', 'Video')
        ],
        validators=[Optional()]
    )

    next_planned_contact_date = DateField(
        'Next Planned Contact Date',
        validators=[Optional()]
    )

    next_planned_contact_type = SelectField(
        'Next Contact Type',
        choices=[
            ('', '-- Select Type --'),
            ('In-person', 'In-person'),
            ('Phone', 'Phone'),
            ('Email', 'Email'),
            ('Video', 'Video')
        ],
        validators=[Optional()]
    )

    submit = SubmitField('Save')
