"""Forms for managing personnel records."""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional


class PersonnelForm(FlaskForm):
    """Create or update a personnel record."""

    full_name = StringField(
        'Full Name',
        validators=[DataRequired(message='Full name is required'), Length(max=255)]
    )

    email = StringField(
        'Email',
        validators=[Optional(), Email(message='Please enter a valid email address.'), Length(max=255)]
    )

    phone = StringField(
        'Phone',
        validators=[Optional(), Length(max=50)]
    )

    role = StringField(
        'Role / Title',
        validators=[Optional(), Length(max=255)]
    )

    # Removed personnel_type field - not needed with new schema

    # Removed organization_type field - relationships are managed through relationship logic

    company_id = SelectField(
        'Company',
        coerce=int,
        choices=[],
        validators=[Optional()]
    )

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=5000)],
        render_kw={'rows': 4}
    )

    is_active = BooleanField('Active')

    submit = SubmitField('Save')


class PersonnelClientLinkForm(FlaskForm):
    """Link a personnel record to a client."""

    client_id = SelectField(
        'Client',
        coerce=int,
        validators=[DataRequired(message='Select a client')]
    )

    role_at_client = StringField(
        'Role at Client',
        validators=[Optional(), Length(max=255)]
    )

    is_primary_contact = BooleanField('Primary Contact')
    is_confidential = BooleanField('Confidential')

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=5000)],
        render_kw={'rows': 3}
    )

    submit = SubmitField('Add Client')

    def __init__(self, client_choices=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if client_choices:
            self.client_id.choices = client_choices
        else:
            self.client_id.choices = []


class InternalPersonnelForm(FlaskForm):
    """Create or update an internal personnel record."""

    full_name = StringField(
        'Full Name',
        validators=[DataRequired(message='Full name is required'), Length(max=255)]
    )

    email = StringField(
        'Email',
        validators=[Optional(), Email(message='Please enter a valid email address.'), Length(max=255)]
    )

    phone = StringField(
        'Phone',
        validators=[Optional(), Length(max=50)]
    )

    role = StringField(
        'Role / Title',
        validators=[Optional(), Length(max=255)]
    )

    department = StringField(
        'Department',
        validators=[Optional(), Length(max=255)]
    )

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=5000)],
        render_kw={'rows': 4}
    )

    is_active = BooleanField('Active')

    submit = SubmitField('Save')


class ExternalPersonnelForm(FlaskForm):
    """Create or update an external personnel record."""

    full_name = StringField(
        'Full Name',
        validators=[DataRequired(message='Full name is required'), Length(max=255)]
    )

    email = StringField(
        'Email',
        validators=[Optional(), Email(message='Please enter a valid email address.'), Length(max=255)]
    )

    phone = StringField(
        'Phone',
        validators=[Optional(), Length(max=50)]
    )

    role = StringField(
        'Role / Title',
        validators=[Optional(), Length(max=255)]
    )

    company_id = SelectField(
        'Company',
        coerce=int,
        choices=[],
        validators=[Optional()]
    )

    contact_type = SelectField(
        'Contact Type',
        choices=[
            ('Primary', 'Primary Contact'),
            ('Secondary', 'Secondary Contact'),
            ('Technical', 'Technical Contact'),
            ('Business', 'Business Contact')
        ],
        validators=[Optional()]
    )

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=5000)],
        render_kw={'rows': 4}
    )

    is_active = BooleanField('Active')

    submit = SubmitField('Save')
