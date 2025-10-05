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

    personnel_type = SelectField(
        'Personnel Type',
        choices=[
            ('Internal', 'Internal (MPR)'),
            ('Client_Contact', 'Client Contact'),
            ('Vendor_Contact', 'Vendor Contact'),
            ('Constructor_Contact', 'Constructor Contact'),
            ('Operator_Contact', 'Operator Contact'),
            ('Other', 'Other'),
        ],
        validators=[DataRequired(message='Select a personnel type')]
    )

    organization_type = SelectField(
        'Organization Type',
        choices=[
            ('', 'None / Internal'),
            ('Owner', 'Owner / Developer'),
            ('Vendor', 'Technology Vendor'),
            ('Operator', 'Operator'),
            ('Constructor', 'Constructor'),
            ('Offtaker', 'Off-taker'),
            ('Client', 'Client'),
            ('Other', 'Other'),
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
