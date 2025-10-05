"""Forms for managing many-to-many relationships"""
from flask_wtf import FlaskForm
from wtforms import (
    SelectField,
    StringField,
    TextAreaField,
    BooleanField,
    DateField,
    HiddenField,
    SubmitField
)
from wtforms.validators import DataRequired, Length, Optional


class VendorSupplierRelationshipForm(FlaskForm):
    """Create a vendor-supplier relationship"""

    supplier_id = SelectField('Supplier', coerce=int, validators=[DataRequired()])
    component_type = StringField('Component Type', validators=[Optional(), Length(max=255)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    is_confidential = BooleanField('Confidential')
    submit = SubmitField('Add Supplier')


class VendorOwnerRelationshipForm(FlaskForm):
    """Link a vendor to an owner/developer"""

    owner_id = SelectField('Owner / Developer', coerce=int, validators=[DataRequired()])
    relationship_type = StringField('Relationship Type', validators=[Optional(), Length(max=255)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    is_confidential = BooleanField('Confidential')
    submit = SubmitField('Add Owner Relationship')


class OwnerVendorRelationshipForm(FlaskForm):
    """Link an owner/developer to a vendor"""

    vendor_id = SelectField('Technology Vendor', coerce=int, validators=[DataRequired()])
    relationship_type = StringField('Relationship Type', validators=[Optional(), Length(max=255)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    is_confidential = BooleanField('Confidential')
    submit = SubmitField('Add Vendor Relationship')


class VendorProjectRelationshipForm(FlaskForm):
    """Associate a vendor with a project"""

    project_id = SelectField('Project', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    is_confidential = BooleanField('Confidential')
    submit = SubmitField('Add Project Relationship')


class ProjectVendorRelationshipForm(FlaskForm):
    """Associate a project with a vendor"""

    vendor_id = SelectField('Vendor', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    is_confidential = BooleanField('Confidential')
    submit = SubmitField('Add Vendor Relationship')


class ProjectConstructorRelationshipForm(FlaskForm):
    """Link a project with a constructor"""

    constructor_id = SelectField('Constructor', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    is_confidential = BooleanField('Confidential')
    submit = SubmitField('Add Constructor')


class ProjectOperatorRelationshipForm(FlaskForm):
    """Link a project with an operator"""

    operator_id = SelectField('Operator', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    is_confidential = BooleanField('Confidential')
    submit = SubmitField('Add Operator')


class ProjectOwnerLinkForm(FlaskForm):
    """Link a project with an owner"""

    owner_id = SelectField('Owner / Developer', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    is_confidential = BooleanField('Confidential')
    submit = SubmitField('Add Owner')


class OwnerProjectRelationshipForm(FlaskForm):
    """Associate an owner with a project"""

    project_id = SelectField('Project', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    is_confidential = BooleanField('Confidential')
    submit = SubmitField('Add Project Relationship')


class ProjectOfftakerRelationshipForm(FlaskForm):
    """Associate a project with an energy off-taker"""

    offtaker_id = SelectField('Off-taker', coerce=int, validators=[DataRequired()])
    agreement_type = StringField('Agreement Type', validators=[Optional(), Length(max=255)])
    contracted_volume = StringField('Contracted Volume', validators=[Optional(), Length(max=255)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    is_confidential = BooleanField('Confidential')
    submit = SubmitField('Add Off-taker')


class VendorPreferredConstructorForm(FlaskForm):
    """Assign a preferred constructor to a vendor"""

    constructor_id = SelectField('Constructor', coerce=int, validators=[DataRequired()])
    preference_reason = TextAreaField('Preference Reason', validators=[Optional(), Length(max=2000)])
    is_confidential = BooleanField('Confidential')
    submit = SubmitField('Add Preferred Constructor')


class PersonnelEntityRelationshipForm(FlaskForm):
    """Link personnel to an entity (context specific)"""

    personnel_id = SelectField('Personnel', coerce=int, validators=[DataRequired()])
    role_at_entity = StringField('Role', validators=[Optional(), Length(max=255)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    is_confidential = BooleanField('Confidential')
    submit = SubmitField('Add Personnel Relationship')


class EntityTeamMemberForm(FlaskForm):
    """Assign internal personnel to an entity"""

    personnel_id = SelectField('Team Member', coerce=int, validators=[DataRequired()])
    assignment_type = SelectField(
        'Assignment Type',
        choices=[
            ('Primary_POC', 'Primary Point of Contact'),
            ('Secondary_POC', 'Secondary Point of Contact'),
            ('Team_Member', 'Team Member')
        ],
        validators=[Optional()]
    )
    assigned_date = DateField('Assigned Date', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Assign Team Member')


class RelationshipDeleteForm(FlaskForm):
    """Generic form for deleting a relationship"""

    relationship_id = HiddenField(validators=[DataRequired()])
    submit = SubmitField('Remove')


class TeamAssignmentToggleForm(FlaskForm):
    """Form to toggle team member assignment active state"""

    assignment_id = HiddenField(validators=[DataRequired()])
    submit = SubmitField('Update Assignment')


class ConfirmActionForm(FlaskForm):
    """Simple form used to confirm destructive actions"""

    submit = SubmitField('Confirm')
