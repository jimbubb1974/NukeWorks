from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)


# ── colour palette ─────────────────────────────────────────────────────────────
DARK_BLUE  = colors.HexColor('#1a3a5c')
MID_BLUE   = colors.HexColor('#2e6da4')
LIGHT_BLUE = colors.HexColor('#dce8f5')
CONF_RED   = colors.HexColor('#8b0000')
CONF_PINK  = colors.HexColor('#fdecea')
NED_PURPLE = colors.HexColor('#5b2c8d')
NED_LIGHT  = colors.HexColor('#f0eaf8')
ROW_ALT    = colors.HexColor('#f4f7fb')
ROW_ALT2   = colors.HexColor('#f8f4fc')
GREY       = colors.HexColor('#666666')


def _styles():
    base = getSampleStyleSheet()
    return {
        'title': ParagraphStyle(
            'Title', parent=base['Title'],
            fontSize=20, textColor=DARK_BLUE, spaceAfter=4,
        ),
        'subtitle': ParagraphStyle(
            'Subtitle', parent=base['Normal'],
            fontSize=9, textColor=GREY, spaceAfter=2,
        ),
        'access_banner': ParagraphStyle(
            'AccessBanner', parent=base['Normal'],
            fontSize=9, textColor=colors.white, backColor=CONF_RED,
            leftIndent=6, rightIndent=6, spaceBefore=4, spaceAfter=4,
        ),
        'section_conf': ParagraphStyle(
            'SectionConf', parent=base['Heading2'],
            fontSize=13, textColor=CONF_RED, spaceBefore=16, spaceAfter=4,
        ),
        'section_ned': ParagraphStyle(
            'SectionNed', parent=base['Heading2'],
            fontSize=13, textColor=NED_PURPLE, spaceBefore=16, spaceAfter=4,
        ),
        'subsection': ParagraphStyle(
            'Subsection', parent=base['Heading3'],
            fontSize=10, textColor=DARK_BLUE, spaceBefore=8, spaceAfter=2,
        ),
        'body': ParagraphStyle(
            'Body', parent=base['Normal'],
            fontSize=8, leading=11,
        ),
        'body_italic': ParagraphStyle(
            'BodyItalic', parent=base['Normal'],
            fontSize=8, leading=11, textColor=GREY, fontName='Helvetica-Oblique',
        ),
        'cell': ParagraphStyle(
            'Cell', parent=base['Normal'],
            fontSize=7.5, leading=10,
        ),
    }


def _hr(color):
    return HRFlowable(width='100%', thickness=1, color=color, spaceAfter=6)


def _fmt_date(d):
    if d is None:
        return '—'
    return d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d)


def _val(v):
    """Return display value, replacing None/empty/redacted with em dash."""
    if v is None or v == '' or v in ('[Confidential]', '[NED Team Only]'):
        return '—'
    return str(v)


def _trunc(v, n=400):
    """Truncate long text for table cells to prevent ReportLab LayoutError."""
    text = _val(v)
    if text == '—':
        return text
    if len(text) > n:
        return text[:n] + '…'
    return text


def _tbl(data, col_widths, header_bg=MID_BLUE, alt_color=ROW_ALT):
    """Build a standard grid table. data[0] is the header row."""
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1,  0), header_bg),
        ('TEXTCOLOR',     (0, 0), (-1,  0), colors.white),
        ('FONTNAME',      (0, 0), (-1,  0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1,  0), 8),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, alt_color]),
        ('GRID',          (0, 0), (-1, -1), 0.25, colors.HexColor('#c0cfe0')),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ('FONTSIZE',      (0, 1), (-1, -1), 7.5),
    ]))
    return t


def _h(text, style):
    return Paragraph(f'<b>{text}</b>', style)


def _p(text, style):
    return Paragraph(_val(text), style)


class ConfidentialDataReport:
    """
    Full-database confidential data dump.
    Sections rendered depend on caller-confirmed permissions:
      - include_tier1: project financials + confidential contact logs
      - include_tier2: client profiles, roundtable history, personnel links
    """

    def __init__(self, user, db_session, generated_by: str,
                 generated_date: datetime,
                 include_tier1: bool, include_tier2: bool):
        self.user = user
        self.db_session = db_session
        self.generated_by = generated_by
        self.generated_date = generated_date
        self.include_tier1 = include_tier1
        self.include_tier2 = include_tier2

    # ── public entry point ────────────────────────────────────────────────────

    def build(self) -> bytes:
        buffer = BytesIO()
        page_w, page_h = landscape(LETTER)
        usable = page_w - 1.7 * inch  # left + right margins

        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(LETTER),
            leftMargin=0.85 * inch, rightMargin=0.85 * inch,
            topMargin=0.75 * inch,  bottomMargin=0.65 * inch,
            title='Confidential Data Report',
        )

        s = _styles()
        story = []

        # ── cover header ──────────────────────────────────────────────────────
        story.append(Paragraph('Confidential Data Report', s['title']))
        story.append(Paragraph(
            f'Generated by: {self.generated_by} &nbsp;|&nbsp; '
            f'Date (UTC): {self.generated_date:%Y-%m-%d %H:%M:%S}',
            s['subtitle'],
        ))

        tiers = []
        if self.include_tier1:
            tiers.append('Tier 1 – Confidential Business Data')
        if self.include_tier2:
            tiers.append('Tier 2 – NED Team Internal Data')
        story.append(Paragraph(
            f'Access level: {" &amp; ".join(tiers)}  '
            '— HANDLE IN ACCORDANCE WITH COMPANY POLICY',
            s['access_banner'],
        ))
        story.append(Spacer(1, 0.1 * inch))
        story.append(_hr(DARK_BLUE))

        # ── Tier 1 sections ───────────────────────────────────────────────────
        if self.include_tier1:
            story += self._project_financials(s, usable)
            story += self._confidential_relationships(s, usable)
            story += self._confidential_contacts(s, usable)

        # ── Tier 2 sections ───────────────────────────────────────────────────
        if self.include_tier2:
            story += self._client_profiles(s, usable)
            story += self._roundtable_history(s, usable)
            story += self._personnel_links(s, usable)

        doc.build(story)
        data = buffer.getvalue()
        buffer.close()
        return data

    # ── Tier 1: project financials ────────────────────────────────────────────

    def _project_financials(self, s, usable):
        from app.models import Project

        projects = (
            self.db_session.query(Project)
            .order_by(Project.project_name)
            .all()
        )

        # Only include projects that have at least one financial field set
        projects = [p for p in projects if any([
            p._capex_encrypted, p._opex_encrypted,
            p._fuel_cost_encrypted, p._lcoe_encrypted,
        ])]

        story = []
        story.append(Paragraph('Project Financial Data', s['section_conf']))
        story.append(_hr(CONF_RED))

        if not projects:
            story.append(Paragraph('No financial data recorded for any project.', s['body_italic']))
            return story

        cw = [usable * f for f in [0.28, 0.14, 0.14, 0.11, 0.11, 0.11, 0.11]]
        header = [_h(t, s['cell']) for t in [
            'Project', 'Location', 'Status', 'CAPEX', 'OPEX', 'Fuel Cost', 'LCOE'
        ]]
        rows = [header]
        for p in projects:
            rows.append([
                _p(p.project_name, s['cell']),
                _p(p.location,     s['cell']),
                _p(p.project_status, s['cell']),
                _p(p.capex,        s['cell']),
                _p(p.opex,         s['cell']),
                _p(p.fuel_cost,    s['cell']),
                _p(p.lcoe,         s['cell']),
            ])

        story.append(_tbl(rows, cw, header_bg=CONF_RED))
        return story

    # ── Tier 1: confidential company-role relationships ───────────────────────

    def _confidential_relationships(self, s, usable):
        from app.models.company import CompanyRoleAssignment, Company, CompanyRole
        from app.models import Project

        from sqlalchemy.orm import joinedload as _jl
        assignments = (
            self.db_session.query(CompanyRoleAssignment)
            .filter(CompanyRoleAssignment.is_confidential == True)   # noqa: E712
            .options(
                _jl(CompanyRoleAssignment.company),
                _jl(CompanyRoleAssignment.role),
            )
            .order_by(CompanyRoleAssignment.context_type,
                      CompanyRoleAssignment.context_id)
            .all()
        )

        story = [Spacer(1, 0.15 * inch)]
        story.append(Paragraph('Confidential Company Relationships', s['section_conf']))
        story.append(_hr(CONF_RED))

        if not assignments:
            story.append(Paragraph('No confidential company relationships found.', s['body_italic']))
            return story

        # Build lookup for projects by id
        projects = {p.project_id: p.project_name
                    for p in self.db_session.query(Project).all()}

        cw = [usable * f for f in [0.24, 0.16, 0.16, 0.22, 0.10, 0.12]]
        header = [_h(t, s['cell']) for t in [
            'Company', 'Role', 'Context', 'Related Entity', 'Primary', 'Notes'
        ]]
        rows = [header]
        for a in assignments:
            company_name = a.company.company_name if a.company else f'ID {a.company_id}'
            role_label   = a.role.role_label if a.role else f'ID {a.role_id}'
            context_type = a.context_type or 'Global'

            if a.context_type == 'Project' and a.context_id:
                related = projects.get(a.context_id, f'Project ID {a.context_id}')
            elif a.context_id:
                related = f'{a.context_type} ID {a.context_id}'
            else:
                related = '—'

            rows.append([
                _p(company_name, s['cell']),
                _p(role_label,   s['cell']),
                _p(context_type, s['cell']),
                _p(related,      s['cell']),
                _p('Yes' if a.is_primary else 'No', s['cell']),
                _p(a.notes,      s['cell']),
            ])

        story.append(_tbl(rows, cw, header_bg=CONF_RED))
        return story

    # ── Tier 1: confidential contact logs ─────────────────────────────────────

    def _confidential_contacts(self, s, usable):
        from app.models import ContactLog, Personnel, Company

        entries = (
            self.db_session.query(ContactLog)
            .filter(ContactLog.is_confidential == True)          # noqa: E712
            .order_by(ContactLog.contact_date.desc())
            .all()
        )

        story = [Spacer(1, 0.15 * inch)]
        story.append(Paragraph('Confidential Contact Log Entries', s['section_conf']))
        story.append(_hr(CONF_RED))

        if not entries:
            story.append(Paragraph('No confidential contact log entries found.', s['body_italic']))
            return story

        # Pre-fetch personnel names
        all_personnel = {p.personnel_id: p.full_name
                         for p in self.db_session.query(Personnel).all()}
        all_companies = {c.company_id: c.company_name
                         for c in self.db_session.query(Company).all()}

        cw = [usable * f for f in [0.10, 0.20, 0.12, 0.16, 0.16, 0.26]]
        header = [_h(t, s['cell']) for t in [
            'Date', 'Company / Entity', 'Type', 'Contacted By', 'Contact Person', 'Summary'
        ]]
        rows = [header]
        for e in entries:
            entity_name = '—'
            if e.entity_type == 'Owner' or e.entity_type == 'Company':
                entity_name = all_companies.get(e.entity_id, f'ID {e.entity_id}')

            contacted_by = all_personnel.get(e.contacted_by, f'ID {e.contacted_by}') \
                if e.contacted_by else '—'
            contact_person = (
                all_personnel.get(e.contact_person_id, f'ID {e.contact_person_id}')
                if e.contact_person_id else e.contact_person_freetext or '—'
            )
            rows.append([
                _p(_fmt_date(e.contact_date),  s['cell']),
                _p(entity_name,                s['cell']),
                _p(e.contact_type,             s['cell']),
                _p(contacted_by,               s['cell']),
                _p(contact_person,             s['cell']),
                Paragraph(_trunc(e.summary), s['cell']),
            ])

        story.append(_tbl(rows, cw, header_bg=CONF_RED))
        return story

    # ── Tier 2: client profiles ───────────────────────────────────────────────

    def _client_profiles(self, s, usable):
        from app.models.company import ClientProfile, Company

        profiles = (
            self.db_session.query(ClientProfile)
            .join(Company, Company.company_id == ClientProfile.company_id)
            .order_by(Company.company_name)
            .all()
        )

        story = [PageBreak()]
        story.append(Paragraph('MPR Client Profiles', s['section_ned']))
        story.append(_hr(NED_PURPLE))

        if not profiles:
            story.append(Paragraph('No client profiles found.', s['body_italic']))
            return story

        cw = [usable * f for f in [0.28, 0.14, 0.14, 0.44]]
        header = [_h(t, s['cell']) for t in [
            'Company', 'Priority', 'Tier', 'Relationship Notes'
        ]]
        rows = [header]
        for prof in profiles:
            company_name = prof.company.company_name if prof.company else f'ID {prof.company_id}'
            rows.append([
                _p(company_name,         s['cell']),
                _p(prof.client_priority, s['cell']),
                _p(prof.client_tier,     s['cell']),
                Paragraph(_trunc(prof.relationship_notes), s['cell']),
            ])

        story.append(_tbl(rows, cw, header_bg=NED_PURPLE, alt_color=ROW_ALT2))
        return story

    # ── Tier 2: roundtable history ────────────────────────────────────────────

    def _roundtable_history(self, s, usable):
        from app.models.roundtable import RoundtableHistory
        from app.models.company import Company
        from app.models import User

        entries = (
            self.db_session.query(RoundtableHistory)
            .filter(RoundtableHistory.entity_type == 'Company')
            .order_by(RoundtableHistory.entity_id,
                      RoundtableHistory.created_timestamp.desc())
            .all()
        )

        story = [Spacer(1, 0.15 * inch)]
        story.append(Paragraph('Roundtable Meeting History', s['section_ned']))
        story.append(_hr(NED_PURPLE))

        if not entries:
            story.append(Paragraph('No roundtable history found.', s['body_italic']))
            return story

        companies = {c.company_id: c.company_name
                     for c in self.db_session.query(Company).all()}
        users = {u.user_id: (u.full_name or u.username)
                 for u in self.db_session.query(User).all()}

        from collections import defaultdict
        by_company = defaultdict(list)
        for e in entries:
            by_company[e.entity_id].append(e)

        label_w = usable * 0.15
        value_w = usable * 0.85

        for company_id, company_entries in sorted(by_company.items()):
            company_name = companies.get(company_id, f'Company ID {company_id}')
            story.append(Paragraph(company_name, s['subsection']))

            for e in company_entries:
                recorded_by = users.get(e.created_by, f'ID {e.created_by}') \
                    if e.created_by else '—'

                # Build a two-column label/value table per entry — flows across pages
                fields = [
                    ('Date',         _fmt_date(e.created_timestamp)),
                    ('Recorded By',  recorded_by),
                    ('Next Steps',   _val(e.next_steps)),
                    ('Client Focus', _val(e.client_near_term_focus)),
                    ('MPR Targets',  _val(e.mpr_work_targets)),
                    ('Discussion',   _val(e.discussion)),
                ]
                # Only include rows with actual content
                rows = [
                    [Paragraph(f'<b>{label}</b>', s['cell']),
                     Paragraph(value, s['cell'])]
                    for label, value in fields
                    if value and value != '—'
                ]
                if not rows:
                    continue

                t = Table(rows, colWidths=[label_w, value_w])
                t.setStyle(TableStyle([
                    ('BACKGROUND',   (0, 0), (0, -1), NED_LIGHT),
                    ('GRID',         (0, 0), (-1, -1), 0.25, colors.HexColor('#c0cfe0')),
                    ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING',   (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
                    ('LEFTPADDING',  (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('FONTSIZE',     (0, 0), (-1, -1), 7.5),
                ]))
                story.append(t)
                story.append(Spacer(1, 0.06 * inch))

            story.append(Spacer(1, 0.08 * inch))

        return story

    # ── Tier 2: personnel relationship links ──────────────────────────────────

    def _personnel_links(self, s, usable):
        from app.models.company import InternalExternalLink, Company
        from app.models import Personnel

        links = (
            self.db_session.query(InternalExternalLink)
            .order_by(InternalExternalLink.internal_person_id)
            .all()
        )

        # Only include links that have encrypted content
        links = [lnk for lnk in links
                 if lnk._relationship_strength_encrypted or lnk._notes_encrypted]

        story = [Spacer(1, 0.15 * inch)]
        story.append(Paragraph('Internal–External Personnel Relationship Assessments', s['section_ned']))
        story.append(_hr(NED_PURPLE))

        if not links:
            story.append(Paragraph(
                'No relationship assessments recorded.', s['body_italic']))
            return story

        personnel = {p.personnel_id: p.full_name
                     for p in self.db_session.query(Personnel).all()}
        companies = {c.company_id: c.company_name
                     for c in self.db_session.query(Company).all()}

        cw = [usable * f for f in [0.19, 0.19, 0.18, 0.14, 0.14, 0.16]]
        header = [_h(t, s['cell']) for t in [
            'Internal (MPR)', 'External Contact', 'Company',
            'Relationship Type', 'Strength', 'Notes'
        ]]
        rows = [header]
        for lnk in links:
            int_name  = personnel.get(lnk.internal_person_id, f'ID {lnk.internal_person_id}')
            ext_name  = personnel.get(lnk.external_person_id, f'ID {lnk.external_person_id}')
            comp_name = companies.get(lnk.company_id, '—') if lnk.company_id else '—'
            rows.append([
                _p(int_name,                  s['cell']),
                _p(ext_name,                  s['cell']),
                _p(comp_name,                 s['cell']),
                _p(lnk.relationship_type,     s['cell']),
                _p(lnk.relationship_strength, s['cell']),
                Paragraph(_trunc(lnk.notes),  s['cell']),
            ])

        story.append(_tbl(rows, cw, header_bg=NED_PURPLE, alt_color=ROW_ALT2))
        return story
