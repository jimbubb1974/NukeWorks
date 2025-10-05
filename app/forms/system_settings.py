"""WTForms for system settings management"""
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Regexp


class CompanySettingsForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(message='Company name is required'),])
    company_logo_path = StringField('Company Logo Path', validators=[Optional()])
    submit = SubmitField('Save Company Settings')


class BackupSettingsForm(FlaskForm):
    auto_snapshot_enabled = BooleanField('Enable Automated Snapshots')
    daily_snapshot_time = StringField(
        'Daily Snapshot Time',
        validators=[
            DataRequired(message='Snapshot time is required'),
            Regexp(r'^(?:[01]\d|2[0-3]):[0-5]\d$', message='Use 24-hour HH:MM format')
        ]
    )
    snapshot_retention_days = IntegerField(
        'Retention Period (days)',
        validators=[DataRequired(message='Retention period required'), NumberRange(min=1, max=3650)]
    )
    max_snapshots = IntegerField(
        'Maximum Snapshots',
        validators=[DataRequired(message='Maximum snapshots required'), NumberRange(min=1, max=500)]
    )
    snapshot_dir = StringField('Snapshot Directory', validators=[Optional()])
    submit = SubmitField('Save Backup Settings')


class CrmSettingsForm(FlaskForm):
    roundtable_history_limit = IntegerField(
        'Roundtable History Limit',
        validators=[DataRequired(message='History limit required'), NumberRange(min=1, max=50)]
    )
    submit = SubmitField('Save CRM Settings')
