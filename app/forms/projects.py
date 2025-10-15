"""Project forms for creating and updating project records."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, DateField, DecimalField, SelectField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Optional, ValidationError, NumberRange
from app import db_session
from app.models import Project


class ProjectForm(FlaskForm):
    """Form used to create or edit a project."""

    project_name = StringField(
        'Project Name',
        validators=[
            DataRequired(message='Project name is required.'),
            Length(max=255, message='Project name cannot exceed 255 characters.')
        ],
        render_kw={'placeholder': 'e.g., Project Alpha'}
    )

    location = StringField(
        'Location',
        validators=[Optional(), Length(max=255, message='Location cannot exceed 255 characters.')],
        render_kw={'placeholder': 'City, State or Country'}
    )

    project_status = StringField(
        'Status',
        validators=[Optional(), Length(max=255, message='Status cannot exceed 255 characters.')],
        render_kw={'placeholder': 'Planning, Construction, Operational, etc.'}
    )

    licensing_approach = StringField(
        'Licensing Approach',
        validators=[Optional(), Length(max=255, message='Licensing approach cannot exceed 255 characters.')],
        render_kw={'placeholder': 'e.g., Part 50, Part 52'}
    )

    configuration = StringField(
        'Configuration',
        validators=[Optional(), Length(max=255, message='Configuration cannot exceed 255 characters.')],
        render_kw={'placeholder': 'Reactor configuration or unit count'}
    )

    project_schedule = TextAreaField(
        'Schedule',
        validators=[Optional(), Length(max=2000, message='Schedule cannot exceed 2,000 characters.')],
        render_kw={'rows': 3, 'placeholder': 'Key milestones or schedule notes'}
    )

    target_cod = DateField(
        'Target COD',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={'type': 'date'}
    )

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=10000, message='Notes cannot exceed 10,000 characters.')],
        render_kw={'rows': 5, 'placeholder': 'Additional project background or commentary'}
    )

    latitude = DecimalField(
        'Latitude',
        places=6,
        rounding=None,
        validators=[Optional(), NumberRange(min=-90, max=90, message='Latitude must be between -90 and 90 degrees.')],
        render_kw={'placeholder': 'e.g., 35.6895'}
    )

    longitude = DecimalField(
        'Longitude',
        places=6,
        rounding=None,
        validators=[Optional(), NumberRange(min=-180, max=180, message='Longitude must be between -180 and 180 degrees.')],
        render_kw={'placeholder': 'e.g., -105.9381'}
    )

    # Financial fields (encrypted - requires confidential access)
    capex = StringField(
        'CAPEX (Capital Expenditure)',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'e.g., 5000000'}
    )

    opex = StringField(
        'OPEX (Operating Expenditure)',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'e.g., 500000 per year'}
    )

    fuel_cost = StringField(
        'Fuel Cost',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'e.g., 10000'}
    )

    lcoe = StringField(
        'LCOE (Levelized Cost of Energy)',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'e.g., 0.085 ($/kWh)'}
    )

    submit = SubmitField('Save Project')

    def __init__(self, project_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_id = project_id

    def validate_project_name(self, field):
        existing = db_session.query(Project).filter(Project.project_name.ilike(field.data.strip())).first()
        if existing and existing.project_id != self.project_id:
            raise ValidationError('A project with this name already exists.')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        lat_provided = self.latitude.data is not None and self.latitude.data != ''
        lon_provided = self.longitude.data is not None and self.longitude.data != ''

        if lat_provided != lon_provided:
            message = 'Provide both latitude and longitude to plot this project on the map.'
            if not lat_provided:
                self.latitude.errors.append(message)
            if not lon_provided:
                self.longitude.errors.append(message)
            return False

        return True


class RelationshipForm(FlaskForm):
    """Form for individual relationship entries."""
    entity_id = SelectField('Entity', coerce=int, validators=[Optional()])
    is_confidential = BooleanField('Confidential', default=False)
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=1000)], render_kw={'rows': 2, 'placeholder': 'Optional relationship notes'})


class ProjectRelationshipForm(FlaskForm):
    """Form for managing project relationships."""
    vendors = FieldList(FormField(RelationshipForm), min_entries=0)
    owners = FieldList(FormField(RelationshipForm), min_entries=0)
    operators = FieldList(FormField(RelationshipForm), min_entries=0)
    constructors = FieldList(FormField(RelationshipForm), min_entries=0)
    offtakers = FieldList(FormField(RelationshipForm), min_entries=0)
