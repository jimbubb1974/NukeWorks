"""
Client Forms (CRM)
WTForms for client CRUD operations with validation
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Length, ValidationError, Optional
from app.utils.validators import (
    validate_string_field,
    ValidationError as CustomValidationError
)


class ClientForm(FlaskForm):
    """Form for creating and editing CRM clients"""

    client_name = StringField(
        'Client Name',
        validators=[
            DataRequired(message="Client name is required"),
            Length(min=1, max=255, message="Client name must be between 1 and 255 characters")
        ],
        render_kw={"placeholder": "e.g., ABC Utility Company, XYZ Consulting"}
    )

    client_type = SelectField(
        'Client Type',
        choices=[
            ('', 'Select...'),
            ('Utility', 'Utility'),
            ('IPP', 'Independent Power Producer (IPP)'),
            ('Government', 'Government'),
            ('Consulting', 'Consulting Firm'),
            ('Other', 'Other')
        ],
        validators=[Optional()]
    )

    notes = TextAreaField(
        'Notes',
        validators=[Length(max=10000, message="Notes cannot exceed 10,000 characters")],
        render_kw={"rows": 5, "placeholder": "General notes about the client"}
    )

    # MPR Points of Contact
    mpr_primary_poc = SelectField(
        'MPR Primary POC',
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()]
    )

    mpr_secondary_poc = SelectField(
        'MPR Secondary POC',
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()]
    )

    submit = SubmitField('Save Client')

    def __init__(self, client_id=None, personnel_choices=None, *args, **kwargs):
        """
        Initialize form

        Args:
            client_id: ID of client being edited (None for new client)
            personnel_choices: List of (id, name) tuples for internal personnel
        """
        super(ClientForm, self).__init__(*args, **kwargs)
        self.client_id = client_id

        # Populate personnel dropdowns with internal MPR team members
        if personnel_choices:
            self.mpr_primary_poc.choices = [('', 'Select...')] + personnel_choices
            self.mpr_secondary_poc.choices = [('', 'Select...')] + personnel_choices
        else:
            self.mpr_primary_poc.choices = [('', 'Select...')]
            self.mpr_secondary_poc.choices = [('', 'Select...')]

    def validate_client_name(self, field):
        """
        Validate client name using custom validators

        Checks:
        - String format and length
        - Trim whitespace
        """
        try:
            # Validate string format
            cleaned_name = validate_string_field(
                field.data,
                "client_name",
                max_length=255,
                required=True
            )

            # Update field data with cleaned value
            field.data = cleaned_name

        except CustomValidationError as e:
            raise ValidationError(str(e))

    def validate_notes(self, field):
        """Validate notes field"""
        if field.data:
            try:
                cleaned_notes = validate_string_field(
                    field.data,
                    "notes",
                    max_length=10000,
                    required=False,
                    allow_newlines=True
                )
                field.data = cleaned_notes
            except CustomValidationError as e:
                raise ValidationError(str(e))


class ClientAssessmentForm(FlaskForm):
    """Form for updating client internal assessment (NED Team only)"""

    relationship_strength = SelectField(
        'Relationship Strength',
        choices=[
            ('', 'Select...'),
            ('Strong', 'Strong'),
            ('Good', 'Good'),
            ('Needs Attention', 'Needs Attention'),
            ('At Risk', 'At Risk'),
            ('New', 'New')
        ],
        validators=[Optional()]
    )

    client_priority = SelectField(
        'Client Priority',
        choices=[
            ('', 'Select...'),
            ('High', 'High'),
            ('Medium', 'Medium'),
            ('Low', 'Low'),
            ('Strategic', 'Strategic'),
            ('Opportunistic', 'Opportunistic')
        ],
        validators=[Optional()]
    )

    client_status = SelectField(
        'Client Status',
        choices=[
            ('', 'Select...'),
            ('Active', 'Active'),
            ('Warm', 'Warm'),
            ('Cold', 'Cold'),
            ('Prospective', 'Prospective')
        ],
        validators=[Optional()]
    )

    relationship_notes = TextAreaField(
        'Relationship Notes',
        validators=[Length(max=10000, message="Notes cannot exceed 10,000 characters")],
        render_kw={"rows": 6, "placeholder": "Internal assessment and strategy notes (NED Team only)"}
    )

    submit = SubmitField('Save Assessment')

    def validate_relationship_notes(self, field):
        """Validate relationship notes field"""
        if field.data:
            try:
                cleaned_notes = validate_string_field(
                    field.data,
                    "relationship_notes",
                    max_length=10000,
                    required=False,
                    allow_newlines=True
                )
                field.data = cleaned_notes
            except CustomValidationError as e:
                raise ValidationError(str(e))


class ClientContactForm(FlaskForm):
    """Form for updating last contact information"""

    last_contact_date = DateField(
        'Last Contact Date',
        validators=[Optional()],
        format='%Y-%m-%d'
    )

    last_contact_type = SelectField(
        'Contact Type',
        choices=[
            ('', 'Select...'),
            ('In-person', 'In-person'),
            ('Phone', 'Phone'),
            ('Email', 'Email'),
            ('Video', 'Video Conference')
        ],
        validators=[Optional()]
    )

    last_contact_by = SelectField(
        'Contacted By',
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()]
    )

    last_contact_notes = TextAreaField(
        'Contact Notes',
        validators=[Length(max=10000, message="Notes cannot exceed 10,000 characters")],
        render_kw={"rows": 3, "placeholder": "Brief summary of the contact"}
    )

    next_planned_contact_date = DateField(
        'Next Planned Contact',
        validators=[Optional()],
        format='%Y-%m-%d'
    )

    next_planned_contact_type = SelectField(
        'Next Contact Type',
        choices=[
            ('', 'Select...'),
            ('In-person', 'In-person'),
            ('Phone', 'Phone'),
            ('Email', 'Email'),
            ('Video', 'Video Conference')
        ],
        validators=[Optional()]
    )

    next_planned_contact_assigned_to = SelectField(
        'Assigned To',
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()]
    )

    submit = SubmitField('Update Contact Info')

    def __init__(self, personnel_choices=None, *args, **kwargs):
        """
        Initialize form

        Args:
            personnel_choices: List of (id, name) tuples for internal personnel
        """
        super(ClientContactForm, self).__init__(*args, **kwargs)

        # Populate personnel dropdowns
        if personnel_choices:
            self.last_contact_by.choices = [('', 'Select...')] + personnel_choices
            self.next_planned_contact_assigned_to.choices = [('', 'Select...')] + personnel_choices
        else:
            self.last_contact_by.choices = [('', 'Select...')]
            self.next_planned_contact_assigned_to.choices = [('', 'Select...')]


class DeleteClientForm(FlaskForm):
    """Form for deleting a client (CSRF protection)"""
    submit = SubmitField('Confirm Delete')
