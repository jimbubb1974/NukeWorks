"""WTForms for Contact Log management"""
from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    HiddenField,
    DateField,
    SelectField,
    StringField,
    TextAreaField,
    BooleanField,
    SubmitField
)
from wtforms.validators import DataRequired, Length, Optional, ValidationError, InputRequired

from app.utils.validators import (
    ValidationError as AppValidationError,
    VALID_CONTACT_TYPES,
    validate_contact_date,
    validate_contact_type,
    validate_contact_person,
    validate_follow_up_date,
    validate_string_field
)


def _build_choices(options, include_placeholder=True, placeholder_label='-- Select --'):
    """Utility to build select choices with optional placeholder"""
    if not include_placeholder:
        return options
    return [('', placeholder_label)] + options


class ContactLogForm(FlaskForm):
    """Form for creating and editing contact log entries"""

    entity_type = HiddenField(validators=[DataRequired(message='Entity type is required')])
    entity_id = HiddenField(validators=[DataRequired(message='Entity id is required')])

    contact_date = DateField('Contact Date', validators=[DataRequired(message='Contact date is required')])
    contact_type = SelectField('Contact Type', choices=[], validators=[DataRequired(message='Contact type is required')])
    contacted_by = SelectField('Your Firm Representative', coerce=int, choices=[], validators=[InputRequired(message='Select who made the contact')])

    contact_person_id = SelectField('Client Contact (from directory)', coerce=int, choices=[], validators=[Optional()])
    contact_person_freetext = StringField('Client Contact (name & title)', validators=[Optional(), Length(max=255)])

    summary = TextAreaField('Summary', validators=[DataRequired(message='Summary is required'), Length(max=5000)])

    follow_up_needed = BooleanField('Follow-up Needed?')
    follow_up_date = DateField('Follow-up Date', validators=[Optional()])
    follow_up_assigned_to = SelectField('Assign Follow-up To', coerce=int, choices=[], validators=[Optional()])

    is_confidential = BooleanField('Mark as Confidential')

    submit = SubmitField('Save Contact Log')

    def __init__(
        self,
        contact_type_choices=None,
        personnel_options=None,
        contact_person_options=None,
        follow_up_personnel_options=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        # Contact types
        contact_type_choices = contact_type_choices or [(value, value) for value in VALID_CONTACT_TYPES]
        self.contact_type.choices = _build_choices(contact_type_choices, placeholder_label='-- Select contact type --')

        # Internal personnel for contacted_by
        personnel_options = personnel_options or []
        self.contacted_by.choices = [(0, '-- Select representative --')] + personnel_options

        # Contact person directory (optional)
        contact_person_options = contact_person_options or []
        # Use numeric placeholder 0 for optional selects to avoid coercion errors
        self.contact_person_id.choices = [(0, '-- Select contact (optional) --')] + contact_person_options

        # Follow-up assignment options (internal personnel)
        follow_up_personnel_options = follow_up_personnel_options or personnel_options
        self.follow_up_assigned_to.choices = [(0, '-- Select assignee --')] + follow_up_personnel_options

    # -------------------------------------------------------------------------
    # Field-level validation hooks
    # -------------------------------------------------------------------------

    def validate_contact_date(self, field):
        try:
            validate_contact_date(field.data)
        except AppValidationError as exc:
            raise ValidationError(str(exc))

    def validate_contact_type(self, field):
        try:
            validate_contact_type(field.data)
        except AppValidationError as exc:
            raise ValidationError(str(exc))

    def validate_contact_person_freetext(self, field):
        if field.data:
            try:
                validate_string_field(field.data, 'contact person', max_length=255, required=False)
            except AppValidationError as exc:
                raise ValidationError(str(exc))

    def validate_summary(self, field):
        try:
            validate_string_field(field.data, 'summary', max_length=5000, required=True, allow_newlines=True)
        except AppValidationError as exc:
            raise ValidationError(str(exc))

    def validate_follow_up_date(self, field):
        if not self.follow_up_needed.data:
            return
        if field.data is None:
            raise ValidationError('Follow-up date is required when scheduling a follow-up')
        try:
            validate_follow_up_date(field.data)
        except AppValidationError as exc:
            raise ValidationError(str(exc))

    def validate_follow_up_assigned_to(self, field):
        if not self.follow_up_needed.data:
            return
        if field.data in (None, 0, ''):
            raise ValidationError('Select who the follow-up is assigned to')

    # -------------------------------------------------------------------------
    # Form-level validation
    # -------------------------------------------------------------------------

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False

        # Contact person validation (rule BL-CL-002)
        contact_person_id = self.contact_person_id.data
        try:
            validated_contact_id = validate_contact_person(contact_person_id, self.contact_person_freetext.data)
            # Normalise 0 -> None for downstream use
            if contact_person_id == 0:
                self.contact_person_id.data = 0
            if validated_contact_id is None:
                self.contact_person_id.data = 0
        except AppValidationError as exc:
            error_msg = str(exc)
            self.contact_person_id.errors.append(error_msg)
            self.contact_person_freetext.errors.append(error_msg)
            return False

        # Ensure contacted_by selection is valid (not placeholder)
        if self.contacted_by.data in (None, '', 0):
            self.contacted_by.errors.append('Select who made the contact')
            return False

        # When follow-up not needed, clear optional fields
        if not self.follow_up_needed.data:
            self.follow_up_date.data = None
            self.follow_up_assigned_to.data = 0

        # Ensure entity_id can be converted to int
        try:
            int(self.entity_id.data)
        except (TypeError, ValueError):
            self.entity_id.errors.append('Invalid entity id')
            return False

        return True
