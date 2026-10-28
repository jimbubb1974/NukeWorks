# Company Document Attachments: Security Maturity Plan

Status: initial version shipped (migration 021). This file tracks the security work we intend to do next so it isn't forgotten.

## What exists today

- Files are copied into a `documents/` folder next to the selected database file (`app/routes/documents.py`, `documents_dir()`), stored under random UUID names. Original names are kept in `company_documents`.
- Metadata lives in the `company_documents` table (`app/models/document.py`).
- Per-file access level: `standard` / `confidential` / `ned`, checked on every list and every open (`can_access_document`). Users cannot set a level above their own.
- Upload and delete require `edit_required`. Delete is a soft delete; the file stays on disk.
- Upload allowlist (`ALLOWED_DOCUMENT_EXTENSIONS` in `config.py`), 16 MB cap, `secure_filename`, MIME type taken from the allowlist (not from the client). SVG/HTML are rejected.
- Served with `X-Content-Type-Options: nosniff` and `Cache-Control: private, no-store`. Only images and PDFs display inline; all else downloads.

## Known gaps (to address)

### 1. Files are not encrypted at rest (highest priority)
Per-field encryption protects database columns, but document files are plain bytes on disk. Anyone with filesystem access to the folder can read them and bypass the access levels.
- Encrypt `confidential` and `ned` files with the existing Fernet key management (`app/utils/key_management.py`), using the matching key type.
- Decide whether `standard` files are also encrypted (simpler and uniform, but files can't be opened outside the app).
- Needs a migration path for existing files and a decision on large-file memory use (Fernet is not streaming; consider chunking).

### 2. Snapshots and backups ignore the `documents/` folder
Snapshots copy only the `.sqlite` file (`app/services/snapshots.py`). A restored snapshot can point at missing files, and copying a database to another machine loses its documents.
- Include `documents/` in snapshots, or add a separate documents backup.
- Ensure restore handles files added after the snapshot (orphans) and missing files.
- Mention it on the admin database settings page until fixed.

### 3. No audit trail for document access
Uploads and deletes are not written to the audit log, and opens/downloads are not recorded at all.
- Log upload, delete and (at least for confidential/NED files) view/download with user, time and document id.

### 4. File content is not inspected
The allowlist trusts the extension. A renamed executable, or a macro-enabled Office file, would be accepted.
- Verify magic bytes against the claimed type.
- Decide policy on legacy Office formats (`.doc`, `.ppt`, `.xls`) and macros.
- Consider antivirus scanning if the deployment has a scanner available.

### 5. Soft-deleted files are never purged
Deleted documents stay on disk and in the table indefinitely, including confidential content.
- Add an admin purge (and optional retention period) that removes the file and row for good.
- Add an admin view of deleted documents with restore.

### 6. Access level is fixed at upload
There is no way to change a document's title, category, description or access level after upload.
- Add an edit action, restricted to the uploader and admins, that is audited. Lowering a level should require extra care.

### 7. Hidden documents are invisible to non-privileged users but still counted nowhere
Unlike relationships (which show a "hidden count"), documents the user cannot see leave no hint. Decide whether that is the desired behavior.

### 8. Filesystem and deployment hardening
- Document where the folder must live and who should have OS-level access to it (especially on shared drives).
- Confirm the folder is excluded from any web-served path or static route.
- Review disk quota / total storage limits and per-company limits.

### 9. Duplicate and integrity handling
SHA-256 is stored but unused.
- Warn on duplicate uploads per company.
- Add an integrity check (admin command) that finds missing files, orphan files and hash mismatches.

## Testing to add
- Access-level checks: standard / confidential / NED users opening each level (list and direct URL).
- Read-only users blocked from upload and delete.
- Disallowed extensions rejected; oversize uploads rejected.
- Cross-company access: a document id requested under the wrong company returns 404.
- Soft-deleted documents return 404.
- Redirect target (`next`) rejects absolute and protocol-relative URLs.

## Suggested order
1. Snapshots include `documents/` (data-loss risk).
2. Audit logging.
3. Encryption at rest for confidential and NED files.
4. Edit/purge/restore admin tooling.
5. Content inspection and integrity check.
6. Tests throughout.
