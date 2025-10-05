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
