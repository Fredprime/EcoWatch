"""Append-only audit trail module."""

from ecowatch.modules.audit.models import AuditEvent
from ecowatch.modules.audit.service import AuditService, record_audit_event

__all__ = ["AuditEvent", "AuditService", "record_audit_event"]
