"""
Authentication routes (login, logout, password management)
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.forms.auth import LoginForm, ChangePasswordForm
from app import db_session
from datetime import datetime
import logging

bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with security features"""
    if current_user.is_authenticated:
        # Always go to DB selector after login page if already authenticated
        try:
            from flask import session as _session
            _session.pop('selected_db_path', None)
        except Exception:
            pass
        return redirect(url_for('db_select.select_database'))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember_me.data

        # Query user
        user = db_session.query(User).filter_by(username=username).first()

        # Check credentials
        if user is None or not user.check_password(password):
            logger.warning(f'Failed login attempt for username: {username} from IP: {request.remote_addr}')
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))

        # Check if account is active
        if not user.is_active:
            logger.warning(f'Login attempt for inactive account: {username}')
            flash('Your account has been deactivated. Please contact an administrator.', 'danger')
            return redirect(url_for('auth.login'))

        # Update last login timestamp
        user.update_last_login()
        db_session.commit()

        # Log user in
        login_user(user, remember=remember)
        logger.info(f'User {username} logged in successfully from IP: {request.remote_addr}')
        flash(f'Welcome back, {user.full_name or user.username}!', 'success')

        # After successful login, always force DB selection
        try:
            from flask import session as _session
            _session.pop('selected_db_path', None)
        except Exception:
            pass
        return redirect(url_for('db_select.select_database'))

    return render_template('auth/login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    """User logout with security logging"""
    username = current_user.username
    logger.info(f'User {username} logged out from IP: {request.remote_addr}')
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change current user's password"""
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('auth.change_password'))

        # Update password
        current_user.set_password(form.new_password.data)
        db_session.commit()

        logger.info(f'User {current_user.username} changed their password')
        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/change_password.html', form=form)


@bp.route('/profile')
@login_required
def profile():
    """View user profile"""
    return render_template('auth/profile.html', user=current_user)
