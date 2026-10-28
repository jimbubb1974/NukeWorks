# Encryption Keys: Setup and Troubleshooting

NukeWorks encrypts sensitive fields in the database with two keys. Everyone who uses a shared database must use **the same two keys**. If a machine uses different keys, anything it saves is unreadable to everyone else, and permanently so unless the original key is found.

| Key (environment variable) | Protects |
|---|---|
| `CONFIDENTIAL_DATA_KEY` | Tier 1: project financials (CAPEX, OPEX, fuel cost, LCOE) |
| `NED_TEAM_KEY` | Tier 2: roundtable entries, client relationship notes, client tier and priority, notes on company role assignments and internal-external links |

Documents attached to companies are **not** encrypted by these keys (see `DOCUMENT_ATTACHMENTS_SECURITY_PLAN.md`).

## Rules

1. **One key pair per team database.** Never generate a second pair "just to get running". The app refuses to start without keys on purpose.
2. **Never commit keys** or paste them into chat, email or tickets. Keep `.env` out of Git.
3. **Back the keys up separately from the database.** A database snapshot does not contain them. If the keys are lost, the encrypted data is gone for good; there is no recovery path.
4. **Treat the keys like passwords.** Store the master copy in your team password manager.

## Setting up a new team (first time only)

One person does this once:

```
python scripts/generate_encryption_keys.py
```

Put the two printed values in the team password manager, then install them on that machine (below). Do not run the generator again for an existing team.

## Joining an existing team (new machine or new user)

1. Get `CONFIDENTIAL_DATA_KEY` and `NED_TEAM_KEY` from the team password manager.
2. Put them in a `.env` file:
   - **Running from source:** in the project root (copy `.env.example`).
   - **Installed or portable app:** in the same folder as `NukeWorks.exe`.
   ```
   CONFIDENTIAL_DATA_KEY=...
   NED_TEAM_KEY=...
   ```
3. Restart the app.
4. Confirm the keys are right (next section).

**Watch for environment variables.** A Windows user- or system-level environment variable with the same name **overrides** the `.env` file. If your keys "don't take", check for stale variables (`$env:NED_TEAM_KEY` in PowerShell).

## Confirming your keys match

Each key has a short fingerprint (the first 8 characters of its hash). It is safe to share, so you can compare fingerprints without exchanging keys. To see yours:

```
python scripts/check_decryption.py "<full path to the .sqlite file>"
```

The first two lines show the fingerprints of the keys loaded on that machine. The same run then tries to decrypt every encrypted value in the database and lists any that fail.

The database also stores the fingerprint pair it was written with (`system_settings.encryption_key_fingerprint`, formatted `conf:xxxxxxxx;ned:xxxxxxxx`). The app compares it with your machine's keys.

## What the app does when keys do not match

If the keys are wrong, or some data in the database cannot be read with your keys, the app:

- shows a red **Encryption key problem** banner on every page;
- **blocks saving** (all create, edit and delete actions) so nothing more is written with the wrong keys;
- still lets you log in and read data, though encrypted fields show `[Decryption Error]`.

A database with no stored fingerprint is checked once: if every encrypted value decrypts with your keys, the fingerprint is recorded automatically. If any value fails, the database stays blocked until it is cleaned or the right keys are installed.

## Fixing a key problem

Work through these in order.

1. **Install the correct team keys** and restart (see "Joining an existing team"). This fixes the usual case, and nothing is lost.
2. **Find out what is unreadable:**
   ```
   python scripts/check_decryption.py "<db>" [--company-id N]
   ```
   Each `FAIL` line says whether the value is encrypted with a different key or is not encrypted data at all. Nothing is changed, and plaintext is never printed.
3. **Look for the old keys.** If the unreadable data was written by someone else, try their keys: set their `CONFIDENTIAL_DATA_KEY` / `NED_TEAM_KEY` in a fresh shell and re-run step 2. If the rows now decrypt, the data is recoverable.
4. **If the old keys are gone, remove the unreadable data:**
   ```
   python scripts/clean_undecryptable.py "<db>"            # dry run: lists what would be removed
   python scripts/clean_undecryptable.py "<db>" --apply    # backs up, cleans, records the fingerprint
   ```
   `--apply` copies the database to `<file>.pre_cleanup_<timestamp>` first, deletes roundtable entries whose encrypted fields are all unreadable, sets other unreadable fields to empty, re-scans, and records your key fingerprint so the app accepts your keys. Make sure nobody else has the app open. Keep the backup for a while; it still contains the removed rows in case old keys turn up.

Do not save new data from a machine with mismatched keys to "work around" the banner. That is exactly how unreadable data gets written.

### Legacy auto-generated keys (May 2026 to 17 June 2026)

Builds from that period auto-generated a private key pair if none were configured and saved it to `encryption_keys.json` in the NukeWorks data folder (by default `%LOCALAPPDATA%\NukeWorks` on Windows, or `NUKEWORKS_DATA_DIR`). Data written by those builds is encrypted with that machine-local pair. If it needs recovering, the file on the machine that wrote it holds the keys (use step 3 above). Once nothing needs recovering, delete the file so nobody mistakes it for the team keys. Current versions no longer read it.

## Changing the team keys on purpose

There is no rotation tool yet. Changing keys means re-encrypting every encrypted value with the old keys and then the new ones; doing it by hand will make the existing data unreadable. Until a rotation tool exists, don't change the keys of a live database. If you ever must re-stamp a database after an intended change, run `clean_undecryptable.py --apply` with the new keys loaded; it records the new fingerprint.

## Notes for developers

- Key loading is in `app/utils/key_management.py`; the fingerprint guard is in `app/utils/key_guard.py`.
- The list of encrypted columns exists in two places and must be kept in sync when a new encrypted column is added: `ENCRYPTED_COLUMNS` in `app/utils/key_guard.py` and `TABLES` in `scripts/check_decryption.py` (the cleanup script reuses the latter).
- The guard skips machines with no keys configured and the test suite, which has none.
