"""Flask route blueprints"""
# Legacy routes removed: operators, constructors, technologies, offtakers (Phase 4 cleanup)
from . import auth, dashboard, projects, companies, crm, reports, admin, contact_log, network, personnel

__all__ = ['auth', 'dashboard', 'projects', 'companies', 'crm', 'reports', 'admin', 'contact_log', 'network', 'personnel']
