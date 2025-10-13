"""Forms for roundtable history management"""
from datetime import date

from flask_wtf import FlaskForm
from wtforms import DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError

from app.utils.validators import validate_meeting_date, validate_string_field, ValidationError as AppValidationError


class RoundtableEntryForm(FlaskForm):
    """Form to add roundtable history entries"""

    meeting_date = DateField('Meeting Date', validators=[DataRequired(message='Meeting date is required')])
    discussion = TextAreaField('Discussion', validators=[DataRequired(message='Discussion is required'), Length(max=10000)])
    action_items = TextAreaField('Action Items', validators=[DataRequired(message='Action items are required'), Length(max=5000)])

    submit = SubmitField('Save Roundtable Entry')

    def validate_meeting_date(self, field):
        try:
            validate_meeting_date(field.data)
        except AppValidationError as exc:
            raise ValidationError(str(exc))

    def validate_discussion(self, field):
        try:
            validate_string_field(field.data, 'discussion', max_length=10000, required=True, allow_newlines=True)
        except AppValidationError as exc:
            raise ValidationError(str(exc))

    def validate_action_items(self, field):
        try:
            validate_string_field(field.data, 'action items', max_length=5000, required=True, allow_newlines=True)
        except AppValidationError as exc:
            raise ValidationError(str(exc))


class RoundtableHistoryForm(FlaskForm):
    """Form for CRM roundtable meeting entries with structured fields"""

    next_steps = TextAreaField(
        'Next Steps',
        validators=[Length(max=10000)],
        render_kw={"placeholder": "Action items and next steps for this client"}
    )

    client_near_term_focus = TextAreaField(
        'Client Near-Term Focus Areas',
        validators=[Length(max=10000)],
        render_kw={"placeholder": "What the client is currently focused on"}
    )

    mpr_work_targets = TextAreaField(
        'MPR Work Targets / Goals',
        validators=[Length(max=10000)],
        render_kw={"placeholder": "MPR's goals and targets for this client relationship"}
    )

    discussion = TextAreaField(
        'General Discussion',
        validators=[Length(max=10000)],
        render_kw={"placeholder": "General discussion notes (optional)"}
    )

    submit = SubmitField('Save Roundtable Entry')
