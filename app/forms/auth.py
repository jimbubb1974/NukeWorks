"""
Authentication forms for login, logout, and password management
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    """Login form for user authentication"""

    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=80)],
        render_kw={'placeholder': 'Enter your username', 'autofocus': True}
    )

    password = PasswordField(
        'Password',
        validators=[DataRequired()],
        render_kw={'placeholder': 'Enter your password'}
    )

    remember_me = BooleanField('Remember Me')

    submit = SubmitField('Sign In')


class ChangePasswordForm(FlaskForm):
    """Form for users to change their password"""

    current_password = PasswordField(
        'Current Password',
        validators=[DataRequired()],
        render_kw={'placeholder': 'Enter your current password'}
    )

    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters long')
        ],
        render_kw={'placeholder': 'Enter new password (min 8 characters)'}
    )

    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(),
            EqualTo('new_password', message='Passwords must match')
        ],
        render_kw={'placeholder': 'Confirm new password'}
    )

    submit = SubmitField('Change Password')


class ForgotPasswordForm(FlaskForm):
    """Form for password reset request (future implementation)"""

    email = StringField(
        'Email Address',
        validators=[DataRequired(), Email()],
        render_kw={'placeholder': 'Enter your email address'}
    )

    submit = SubmitField('Request Password Reset')


class CreateUserForm(FlaskForm):
    """Form for admins to create new users"""

    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=80)],
        render_kw={'placeholder': 'Enter username'}
    )

    email = StringField(
        'Email',
        validators=[DataRequired(), Email(), Length(max=120)],
        render_kw={'placeholder': 'Enter email address'}
    )

    full_name = StringField(
        'Full Name',
        validators=[Length(max=120)],
        render_kw={'placeholder': 'Enter full name (optional)'}
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters long')
        ],
        render_kw={'placeholder': 'Enter password (min 8 characters)'}
    )

    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ],
        render_kw={'placeholder': 'Confirm password'}
    )

    has_confidential_access = BooleanField('Confidential Access (Tier 1)')
    is_ned_team = BooleanField('NED Team Access (Tier 2)')
    is_admin = BooleanField('Administrator')
    is_active = BooleanField('Active', default=True)

    submit = SubmitField('Create User')

    def validate_username(self, username):
        """Check if username already exists"""
        from app import db_session
        user = db_session.query(User).filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

    def validate_email(self, email):
        """Check if email already exists"""
        from app import db_session
        user = db_session.query(User).filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')


class EditUserForm(FlaskForm):
    """Form for admins to edit existing users"""

    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=80)],
        render_kw={'readonly': True}  # Username shouldn't be changed
    )

    email = StringField(
        'Email',
        validators=[DataRequired(), Email(), Length(max=120)],
        render_kw={'placeholder': 'Enter email address'}
    )

    full_name = StringField(
        'Full Name',
        validators=[Length(max=120)],
        render_kw={'placeholder': 'Enter full name (optional)'}
    )

    has_confidential_access = BooleanField('Confidential Access (Tier 1)')
    is_ned_team = BooleanField('NED Team Access (Tier 2)')
    is_admin = BooleanField('Administrator')
    is_active = BooleanField('Active')

    submit = SubmitField('Update User')


class AdminChangePasswordForm(FlaskForm):
    """Admin form to set a user's password without current password"""

    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters long')
        ],
        render_kw={'placeholder': 'Enter new password (min 8 characters)'}
    )

    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(),
            EqualTo('new_password', message='Passwords must match')
        ],
        render_kw={'placeholder': 'Confirm new password'}
    )

    submit = SubmitField('Change Password')
