"""Company document attachments: upload, view/download, delete."""
import hashlib
import uuid
from datetime import datetime
from pathlib import Path

from flask import (
    Blueprint, current_app, flash, g, redirect, request, send_file, url_for, abort
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db_session
from app.models import Company, CompanyDocument
from app.models.document import ACCESS_LEVELS, CATEGORIES
from app.utils.permissions import edit_required, can_view_ned_content

bp = Blueprint('documents', __name__, url_prefix='/companies')


def documents_dir() -> Path:
    """Folder holding document files for the currently selected database."""
    db_path = getattr(g, 'selected_db_path', None)
    if db_path:
        path = Path(db_path).resolve().parent / 'documents'
    else:
        path = Path(current_app.config['UPLOAD_FOLDER']) / 'documents'
    path.mkdir(parents=True, exist_ok=True)
    return path


def can_access_document(user, doc: CompanyDocument) -> bool:
    if getattr(user, 'is_admin', False):
        return True
    if doc.access_level == 'ned':
        return can_view_ned_content(user)
    if doc.access_level == 'confidential':
        return bool(getattr(user, 'has_confidential_access', False))
    return True


def visible_documents(user, company_id: int) -> list[CompanyDocument]:
    docs = (
        db_session.query(CompanyDocument)
        .filter_by(company_id=company_id, is_deleted=0)
        .order_by(CompanyDocument.uploaded_at.desc())
        .all()
    )
    return [d for d in docs if can_access_document(user, d)]


def _back(company_id):
    target = request.form.get('next', '')
    # Only allow same-site relative redirects
    if target.startswith('/') and not target.startswith('//'):
        return redirect(target)
    return redirect(url_for('companies.view_company', company_id=company_id))


@bp.route('/<int:company_id>/documents/upload', methods=['POST'])
@login_required
@edit_required
def upload_document(company_id):
    company = db_session.get(Company, company_id)
    if not company:
        abort(404)

    upload = request.files.get('file')
    if not upload or not upload.filename:
        flash('Please choose a file to upload.', 'warning')
        return _back(company_id)

    original = secure_filename(upload.filename) or 'file'
    ext = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    allowed = current_app.config['ALLOWED_DOCUMENT_EXTENSIONS']
    if ext not in allowed:
        flash(f'File type ".{ext}" is not allowed.', 'danger')
        return _back(company_id)

    access_level = request.form.get('access_level', 'standard')
    if access_level not in ACCESS_LEVELS:
        access_level = 'standard'
    # Users can't create documents at a level they couldn't view themselves
    if not can_access_document(current_user, CompanyDocument(access_level=access_level)):
        flash('You cannot set an access level higher than your own.', 'danger')
        return _back(company_id)

    category = request.form.get('category') or None
    if category not in CATEGORIES:
        category = None
    title = (request.form.get('title') or '').strip() or original

    stored = f'{uuid.uuid4().hex}.{ext}'
    dest = documents_dir() / stored
    sha = hashlib.sha256()
    size = 0
    try:
        with open(dest, 'wb') as fh:
            for chunk in iter(lambda: upload.stream.read(1024 * 1024), b''):
                sha.update(chunk)
                size += len(chunk)
                fh.write(chunk)

        db_session.add(CompanyDocument(
            company_id=company_id,
            title=title,
            description=(request.form.get('description') or '').strip() or None,
            category=category,
            access_level=access_level,
            original_filename=original,
            stored_filename=stored,
            mime_type=allowed[ext],
            size_bytes=size,
            sha256=sha.hexdigest(),
            uploaded_by=current_user.user_id,
            uploaded_at=datetime.utcnow(),
        ))
        db_session.commit()
        flash(f'Uploaded "{title}".', 'success')
    except Exception as exc:
        db_session.rollback()
        dest.unlink(missing_ok=True)
        flash(f'Error uploading document: {exc}', 'danger')
    return _back(company_id)


def _get_doc_or_404(company_id, document_id) -> CompanyDocument:
    doc = db_session.get(CompanyDocument, document_id)
    if not doc or doc.company_id != company_id or doc.is_deleted:
        abort(404)
    if not can_access_document(current_user, doc):
        abort(403)
    return doc


@bp.route('/<int:company_id>/documents/<int:document_id>')
@login_required
def view_document(company_id, document_id):
    """Open images/PDFs inline; everything else downloads."""
    doc = _get_doc_or_404(company_id, document_id)
    path = documents_dir() / doc.stored_filename
    if not path.is_file():
        flash('The file for this document is missing from disk.', 'danger')
        return redirect(url_for('companies.view_company', company_id=company_id))

    resp = send_file(
        path,
        mimetype=doc.mime_type or 'application/octet-stream',
        as_attachment=not doc.is_inline or request.args.get('download') == '1',
        download_name=doc.original_filename,
    )
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['Cache-Control'] = 'private, no-store'
    return resp


@bp.route('/<int:company_id>/documents/<int:document_id>/delete', methods=['POST'])
@login_required
@edit_required
def delete_document(company_id, document_id):
    doc = _get_doc_or_404(company_id, document_id)
    # Soft delete: the file stays on disk so a mistake is recoverable
    doc.is_deleted = 1
    doc.deleted_at = datetime.utcnow()
    doc.deleted_by = current_user.user_id
    try:
        db_session.commit()
        flash(f'Removed "{doc.title}".', 'success')
    except Exception as exc:
        db_session.rollback()
        flash(f'Error removing document: {exc}', 'danger')
    return _back(company_id)
