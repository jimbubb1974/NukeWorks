"""Forms for managing database snapshots"""
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, HiddenField
from wtforms.validators import Length, Optional


class ManualSnapshotForm(FlaskForm):
    description = StringField('Description', validators=[Optional(), Length(max=255)])
    retain = BooleanField('Retain snapshot (prevent auto-delete)')
    submit = SubmitField('Create Snapshot')


class SnapshotActionForm(FlaskForm):
    snapshot_id = HiddenField()
    submit = SubmitField('Confirm')
