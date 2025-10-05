"""
Client Relationship Forms
Forms for managing client relationships to owners, projects, vendors, operators, personnel
"""
from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField, StringField, BooleanField
from wtforms.validators import DataRequired, Optional, Length


class ClientOwnerRelationshipForm(FlaskForm):
    """Form for linking a client to an owner/developer"""

    owner_id = SelectField(
        'Owner/Developer',
        coerce=lambda x: int(x) if x else None,
        validators=[DataRequired(message="Please select an owner/developer")]
    )

    notes = TextAreaField(
        'Notes',
        validators=[Length(max=5000, message="Notes cannot exceed 5,000 characters")],
        render_kw={"rows": 3, "placeholder": "Notes about this relationship"}
    )

    submit = SubmitField('Add Owner/Developer')

    def __init__(self, owner_choices=None, *args, **kwargs):
        super(ClientOwnerRelationshipForm, self).__init__(*args, **kwargs)
        if owner_choices:
            self.owner_id.choices = [('', 'Select...')] + owner_choices
        else:
            self.owner_id.choices = [('', 'Select...')]


class ClientProjectRelationshipForm(FlaskForm):
    """Form for linking a client to a project"""

    project_id = SelectField(
        'Project',
        coerce=lambda x: int(x) if x else None,
        validators=[DataRequired(message="Please select a project")]
    )

    relationship_type = SelectField(
        'Relationship Type',
        choices=[
            ('', 'Select...'),
            ('Owner', 'Owner'),
            ('Consultant', 'Consultant'),
            ('Advisor', 'Advisor'),
            ('Stakeholder', 'Stakeholder'),
            ('Other', 'Other')
        ],
        validators=[Optional()]
    )

    notes = TextAreaField(
        'Notes',
        validators=[Length(max=5000, message="Notes cannot exceed 5,000 characters")],
        render_kw={"rows": 3, "placeholder": "Notes about this relationship"}
    )

    submit = SubmitField('Add Project')

    def __init__(self, project_choices=None, *args, **kwargs):
        super(ClientProjectRelationshipForm, self).__init__(*args, **kwargs)
        if project_choices:
            self.project_id.choices = [('', 'Select...')] + project_choices
        else:
            self.project_id.choices = [('', 'Select...')]


class ClientVendorRelationshipForm(FlaskForm):
    """Form for linking a client to a technology vendor"""

    vendor_id = SelectField(
        'Technology Vendor',
        coerce=lambda x: int(x) if x else None,
        validators=[DataRequired(message="Please select a technology vendor")]
    )

    notes = TextAreaField(
        'Notes',
        validators=[Length(max=5000, message="Notes cannot exceed 5,000 characters")],
        render_kw={"rows": 3, "placeholder": "Notes about this relationship"}
    )

    submit = SubmitField('Add Technology Vendor')

    def __init__(self, vendor_choices=None, *args, **kwargs):
        super(ClientVendorRelationshipForm, self).__init__(*args, **kwargs)
        if vendor_choices:
            self.vendor_id.choices = [('', 'Select...')] + vendor_choices
        else:
            self.vendor_id.choices = [('', 'Select...')]


class ClientOperatorRelationshipForm(FlaskForm):
    """Form for linking a client to an operator"""

    operator_id = SelectField(
        'Operator',
        coerce=lambda x: int(x) if x else None,
        validators=[DataRequired(message="Please select an operator")]
    )

    notes = TextAreaField(
        'Notes',
        validators=[Length(max=5000, message="Notes cannot exceed 5,000 characters")],
        render_kw={"rows": 3, "placeholder": "Notes about this relationship"}
    )

    submit = SubmitField('Add Operator')

    def __init__(self, operator_choices=None, *args, **kwargs):
        super(ClientOperatorRelationshipForm, self).__init__(*args, **kwargs)
        if operator_choices:
            self.operator_id.choices = [('', 'Select...')] + operator_choices
        else:
            self.operator_id.choices = [('', 'Select...')]


class ClientPersonnelRelationshipForm(FlaskForm):
    """Form for linking a client to key personnel"""

    personnel_id = SelectField(
        'Personnel',
        coerce=lambda x: int(x) if x else None,
        validators=[DataRequired(message="Please select a person")]
    )

    role_at_client = StringField(
        'Role at Client',
        validators=[Length(max=255, message="Role cannot exceed 255 characters")],
        render_kw={"placeholder": "e.g., VP of Engineering, Project Manager"}
    )

    is_primary_contact = BooleanField(
        'Primary Contact at Client'
    )

    mpr_relationship_strength = SelectField(
        'MPR Relationship Strength',
        choices=[
            ('', 'Select...'),
            ('Strong', 'Strong'),
            ('Good', 'Good'),
            ('Developing', 'Developing'),
            ('New', 'New'),
            ('Unknown', 'Unknown')
        ],
        validators=[Optional()]
    )

    notes = TextAreaField(
        'Notes',
        validators=[Length(max=5000, message="Notes cannot exceed 5,000 characters")],
        render_kw={"rows": 3, "placeholder": "Notes about this person and relationship"}
    )

    submit = SubmitField('Add Key Personnel')

    def __init__(self, personnel_choices=None, *args, **kwargs):
        super(ClientPersonnelRelationshipForm, self).__init__(*args, **kwargs)
        if personnel_choices:
            self.personnel_id.choices = [('', 'Select...')] + personnel_choices
        else:
            self.personnel_id.choices = [('', 'Select...')]


class RemoveRelationshipForm(FlaskForm):
    """Simple form for removing a relationship (CSRF protection)"""
    submit = SubmitField('Remove')
