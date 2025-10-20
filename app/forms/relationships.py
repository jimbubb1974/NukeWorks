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


class ProjectCompanyRelationshipForm(FlaskForm):
    """Associate a project with a company"""

    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])
    role_type = SelectField(
        'Role Type',
        coerce=str,
        validators=[DataRequired()],
        # Normalize Owner/Developer to submit 'developer' internally
        choices=[
            ('vendor', 'Vendor'),
            ('constructor', 'Constructor'),
            ('operator', 'Operator'),
            ('developer', 'Owner/Developer'),
            ('offtaker', 'Offtaker')
        ]
    )
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    is_confidential = BooleanField('Confidential')
    submit = SubmitField('Add Company Relationship')


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
