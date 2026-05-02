"""
Research workflow blueprint.
Handles export package generation, AI response import, and staged review queue.
"""
import json
import io
import zipfile
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, g
from flask_login import login_required, current_user

from app.utils.permissions import ned_team_required

bp = Blueprint('research', __name__, url_prefix='/research')


def _db():
    return g.db_session


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

@bp.route('/')
@ned_team_required
def index():
    from app.forms.research import ExportForm, ImportForm
    from app.models import Company, ResearchImportRun
    from app.services.research_export import get_export_stats, recommended_chunk_count

    export_form = ExportForm()
    import_form = ImportForm()

    stats = get_export_stats(_db())
    suggested_chunks = recommended_chunk_count(stats)

    runs = (
        _db().query(ResearchImportRun)
        .order_by(ResearchImportRun.created_at.desc())
        .limit(20)
        .all()
    )

    companies = (
        _db().query(Company)
        .filter(Company.is_internal == False)
        .order_by(Company.company_name)
        .all()
    )

    prompt_text = _load_prompt_text()

    return render_template(
        'research/index.html',
        export_form=export_form,
        import_form=import_form,
        stats=stats,
        suggested_chunks=suggested_chunks,
        runs=runs,
        companies=companies,
        prompt_text=prompt_text,
    )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@bp.route('/export', methods=['POST'])
@ned_team_required
def export():
    from app.forms.research import ExportForm
    from app.services.research_export import build_export_chunks

    form = ExportForm()
    if not form.validate_on_submit():
        flash('Invalid export parameters.', 'danger')
        return redirect(url_for('research.index'))

    scope = form.scope.data
    chunk_size = form.chunk_size.data

    # Collect selected company IDs if scope == 'selected'
    company_ids = None
    if scope == 'selected':
        raw = request.form.getlist('selected_company_ids')
        company_ids = [int(x) for x in raw if x.isdigit()]
        if not company_ids:
            flash('No companies selected. Choose at least one or use "All entities".', 'warning')
            return redirect(url_for('research.index'))

    chunks = build_export_chunks(_db(), company_ids=company_ids, chunk_size=chunk_size)

    if not chunks:
        flash('No exportable entities found with the current filters.', 'warning')
        return redirect(url_for('research.index'))

    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M')
    prompt_text = _load_prompt_text()

    # Always produce a zip so the prompt is always included alongside the data
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Include the plain prompt as a standalone file for easy copy-paste
        zf.writestr('research_prompt.txt', prompt_text)
        for chunk in chunks:
            n = chunk['metadata']['chunk']
            total = chunk['metadata']['total_chunks']
            fname = (
                f'research_package_{timestamp}.json'
                if total == 1
                else f'research_package_{n}of{total}_{timestamp}.json'
            )
            # Strip the embedded instructions from the JSON — they're in the
            # separate txt file; keeping them in the JSON too would double the
            # payload size and distract the agent from the data block.
            chunk_clean = {k: v for k, v in chunk.items() if k != 'instructions'}
            zf.writestr(fname, json.dumps(chunk_clean, indent=2, ensure_ascii=False))
    zip_buf.seek(0)
    return send_file(
        zip_buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'research_package_{timestamp}.zip',
    )


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

@bp.route('/import', methods=['POST'])
@ned_team_required
def import_response():
    from app.forms.research import ImportForm
    from app.models import ResearchImportRun
    from app.services.research_import import parse_and_stage

    form = ImportForm()
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for e in errors:
                flash(f'{e}', 'danger')
        return redirect(url_for('research.index'))

    run_name = form.run_name.data.strip()
    uploaded_file = form.response_file.data

    try:
        raw = uploaded_file.read().decode('utf-8')
        payload = _extract_json(raw)
    except Exception as e:
        flash(f'Could not read uploaded file: {e}', 'danger')
        return redirect(url_for('research.index'))

    # Create the import run record
    run = ResearchImportRun(
        run_name=run_name,
        created_by=current_user.user_id,
        chunk_count=1,
    )
    _db().add(run)
    _db().flush()  # get run_id

    try:
        item_count = parse_and_stage(payload, run.run_id, _db())
    except ValueError as e:
        _db().rollback()
        flash(f'Import failed — {e}', 'danger')
        return redirect(url_for('research.index'))

    run.total_items = item_count
    _db().commit()

    flash(f'Imported {item_count} proposed change(s) staged for review.', 'success')
    return redirect(url_for('research.run_detail', run_id=run.run_id))


# ---------------------------------------------------------------------------
# Review queue
# ---------------------------------------------------------------------------

@bp.route('/runs/<int:run_id>')
@ned_team_required
def run_detail(run_id):
    from app.models import ResearchImportRun, ResearchQueueItem

    run = _db().query(ResearchImportRun).get(run_id)
    if not run:
        flash('Research run not found.', 'danger')
        return redirect(url_for('research.index'))

    items = (
        _db().query(ResearchQueueItem)
        .filter(ResearchQueueItem.run_id == run_id)
        .order_by(ResearchQueueItem.change_type, ResearchQueueItem.entity_type, ResearchQueueItem.entity_name)
        .all()
    )

    # Group for template
    grouped = {'conflict': [], 'update': [], 'new': []}
    for item in items:
        grouped.setdefault(item.change_type, []).append(item)

    return render_template(
        'research/run_detail.html',
        run=run,
        grouped=grouped,
        pending_count=sum(1 for i in items if i.status == 'pending'),
    )


@bp.route('/runs/<int:run_id>/items/<int:item_id>/accept', methods=['POST'])
@login_required
def accept_item(run_id, item_id):
    from app.models import ResearchImportRun, ResearchQueueItem
    from app.services.research_import import apply_queue_item

    if not current_user.can_edit():
        flash('Read-only accounts cannot accept research items.', 'danger')
        return redirect(url_for('research.run_detail', run_id=run_id))

    item = _db().query(ResearchQueueItem).filter_by(item_id=item_id, run_id=run_id).first()
    if not item or item.status != 'pending':
        flash('Item not found or already reviewed.', 'warning')
        return redirect(url_for('research.run_detail', run_id=run_id))

    # For update/conflict items, build a per-field dict from the form checkboxes.
    # For new items, fields_to_apply stays None (apply_queue_item uses all proposed fields).
    fields_to_apply = None
    if item.change_type in ('update', 'conflict'):
        selected_fields = request.form.getlist('fields')
        if not selected_fields:
            flash('No fields selected — nothing to apply.', 'warning')
            return redirect(url_for('research.run_detail', run_id=run_id))
        proposed = item.get_proposed()
        fields_to_apply = {}
        for field in selected_fields:
            use_custom = request.form.get(f'use_custom_{field}', '0') == '1'
            if use_custom:
                val = request.form.get(f'custom_value_{field}', '').strip() or None
            else:
                val = proposed.get(field)
            fields_to_apply[field] = val

    try:
        apply_queue_item(item, _db(), current_user.user_id, fields_to_apply=fields_to_apply)
        item.status = 'accepted'
        item.reviewed_at = datetime.utcnow()
        item.reviewed_by = current_user.user_id
        _update_run_counts(run_id)
        _db().commit()
        flash(f'Accepted: {item.entity_name}', 'success')
    except Exception as e:
        _db().rollback()
        flash(f'Failed to apply change: {e}', 'danger')

    anchor = _next_pending_anchor(run_id, item_id)
    return redirect(url_for('research.run_detail', run_id=run_id, _anchor=anchor) if anchor
                    else url_for('research.run_detail', run_id=run_id))


@bp.route('/runs/<int:run_id>/items/<int:item_id>/skip', methods=['POST'])
@login_required
def skip_item(run_id, item_id):
    from app.models import ResearchImportRun, ResearchQueueItem

    if not current_user.can_edit():
        flash('Read-only accounts cannot skip research items.', 'danger')
        return redirect(url_for('research.run_detail', run_id=run_id))

    item = _db().query(ResearchQueueItem).filter_by(item_id=item_id, run_id=run_id).first()
    if not item or item.status != 'pending':
        flash('Item not found or already reviewed.', 'warning')
        return redirect(url_for('research.run_detail', run_id=run_id))

    item.status = 'skipped'
    item.reviewed_at = datetime.utcnow()
    item.reviewed_by = current_user.user_id
    _update_run_counts(run_id)
    _db().commit()

    anchor = _next_pending_anchor(run_id, item_id)
    return redirect(url_for('research.run_detail', run_id=run_id, _anchor=anchor) if anchor
                    else url_for('research.run_detail', run_id=run_id))


@bp.route('/runs/<int:run_id>/delete', methods=['POST'])
@login_required
def delete_run(run_id):
    from app.models import ResearchImportRun, ResearchQueueItem

    if not current_user.can_edit():
        flash('Read-only accounts cannot delete research runs.', 'danger')
        return redirect(url_for('research.index'))

    run = _db().query(ResearchImportRun).get(run_id)
    if not run:
        flash('Run not found.', 'danger')
        return redirect(url_for('research.index'))

    run_name = run.run_name
    _db().query(ResearchQueueItem).filter_by(run_id=run_id).delete()
    _db().delete(run)
    _db().commit()

    flash(f'Deleted run "{run_name}".', 'info')
    return redirect(url_for('research.index'))


@bp.route('/runs/<int:run_id>/skip-all', methods=['POST'])
@login_required
def skip_all(run_id):
    from app.models import ResearchQueueItem

    if not current_user.can_edit():
        flash('Read-only accounts cannot skip research items.', 'danger')
        return redirect(url_for('research.run_detail', run_id=run_id))

    now = datetime.utcnow()
    pending = (
        _db().query(ResearchQueueItem)
        .filter_by(run_id=run_id, status='pending')
        .all()
    )
    for item in pending:
        item.status = 'skipped'
        item.reviewed_at = now
        item.reviewed_by = current_user.user_id

    _update_run_counts(run_id)
    _db().commit()
    flash(f'Skipped {len(pending)} remaining item(s).', 'info')
    return redirect(url_for('research.run_detail', run_id=run_id))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@bp.route('/prompt')
@ned_team_required
def download_prompt():
    """Download the current research prompt as a plain text file."""
    prompt_text = _load_prompt_text()
    buf = io.BytesIO(prompt_text.encode('utf-8'))
    buf.seek(0)
    return send_file(
        buf,
        mimetype='text/plain',
        as_attachment=True,
        download_name='research_prompt.txt',
    )


def _load_prompt_text() -> str:
    from pathlib import Path
    prompt_path = Path(__file__).parent.parent.parent / 'docs' / 'research_prompt.txt'
    try:
        return prompt_path.read_text(encoding='utf-8')
    except Exception:
        return '(Prompt file not found — check docs/research_prompt.txt)'


def _update_run_counts(run_id):
    from app.models import ResearchImportRun, ResearchQueueItem
    run = _db().query(ResearchImportRun).get(run_id)
    if not run:
        return
    items = _db().query(ResearchQueueItem).filter_by(run_id=run_id).all()
    run.accepted_items = sum(1 for i in items if i.status == 'accepted')
    run.skipped_items = sum(1 for i in items if i.status == 'skipped')
    pending = sum(1 for i in items if i.status == 'pending')
    if pending == 0:
        run.status = 'complete'


def _next_pending_anchor(run_id: int, acted_item_id: int) -> str:
    """Return anchor fragment for the next pending item after acted_item_id.

    Looks forward in the sorted list; wraps to the first pending item if none
    follow the acted item. Returns '' when no pending items remain.
    """
    from app.models import ResearchQueueItem
    items = (
        _db().query(ResearchQueueItem)
        .filter(ResearchQueueItem.run_id == run_id)
        .order_by(ResearchQueueItem.change_type, ResearchQueueItem.entity_type, ResearchQueueItem.entity_name)
        .all()
    )
    ids = [i.item_id for i in items]
    pos = ids.index(acted_item_id) if acted_item_id in ids else -1
    for item in items[pos + 1:]:
        if item.status == 'pending':
            return f'item-{item.item_id}'
    for item in items:
        if item.status == 'pending':
            return f'item-{item.item_id}'
    return ''


def _extract_json(raw: str) -> dict:
    """
    Parse JSON from raw text, tolerating markdown code fences and leading/trailing prose.
    Raises ValueError with a descriptive message if parsing fails.
    """
    text = raw.strip()

    # Strip markdown code fences
    if text.startswith('```'):
        lines = text.splitlines()
        # Drop first line (```json or ```) and last line (```)
        inner = lines[1:-1] if lines[-1].strip() == '```' else lines[1:]
        text = '\n'.join(inner).strip()

    # Find the outermost { ... } block in case the agent added prose around it
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            'No JSON object found in file. '
            'The file must contain a single JSON object starting with { and ending with }.'
        )
    text = text[start:end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f'Invalid JSON: {e}')
