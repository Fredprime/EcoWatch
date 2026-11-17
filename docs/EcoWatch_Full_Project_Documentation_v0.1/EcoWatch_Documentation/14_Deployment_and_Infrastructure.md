# 14 — Deployment and Infrastructure Design

**Status:** Planning document only. Deployment is deferred until design, requirements, budget and operating responsibilities are approved.

## 1. Purpose

This document records the infrastructure questions that must be answered before EcoWatch is deployed. It is not a deployment guide and does not select a hosting provider.

## 2. Deployment principles

- Keep the pilot architecture simple.
- Separate development, testing and production environments.
- Protect secrets and credentials.
- Use encrypted connections.
- Back up structured data and uploaded evidence.
- Monitor application errors, storage, processing queues and database health.
- Document recovery procedures.
- Keep infrastructure reproducible and changes reviewed.
- Avoid expensive infrastructure without a demonstrated need.

## 3. Environment separation

### Development
Used for local development and test data. Real sensitive community submissions should not be copied here without an approved protection process.

### Testing/staging
Used to validate releases and integrations with representative non-sensitive data.

### Production
Used for real submissions and operational records. Access should be restricted, monitored and backed up.

## 4. Infrastructure components to plan

- Web application hosting.
- Backend/API hosting.
- PostgreSQL hosting and administration.
- File/object storage.
- Background processing for imports and analysis.
- Authentication and account recovery.
- Domain and TLS certificates.
- Monitoring and error reporting.
- Backup and recovery.
- Email or notification delivery, if approved.

Specific providers are not selected.

## 5. Hosting region and data location

Evaluate data residency, latency, cost, contractual terms, backup location and applicable Ghanaian legal obligations. Do not assume a provider's default region is appropriate.

## 6. Reliability and recovery

Define:
- Recovery point objective (how much recent data loss could be tolerated).
- Recovery time objective (how quickly the service should return).
- Backup frequency and retention.
- Database and media restoration procedures.
- Who can initiate recovery.
- How restoration is tested.

The targets must match the pilot's importance and budget.

## 7. Security operations

Before launch:
- Configure least-privilege access.
- Store secrets outside source code.
- Enable appropriate logging.
- Patch supported software.
- Review exposed services.
- Protect administrative accounts.
- Establish an incident response contact.
- Test access revocation.

## 8. Cost controls

Estimate monthly and one-off costs for database, compute, storage, bandwidth, backups, map services, data processing, email and monitoring. Include growth assumptions for uploaded video and imagery. Large media and geospatial processing may dominate costs.

## 9. Deployment readiness checklist

- [ ] Scope and pilot location approved.
- [ ] Data permissions reviewed.
- [ ] Privacy and security review completed.
- [ ] Database schema reviewed and migrations tested.
- [ ] Upload controls tested.
- [ ] Backups configured and restore tested.
- [ ] Monitoring and alert ownership assigned.
- [ ] User roles and administrator access reviewed.
- [ ] Support and escalation process documented.
- [ ] User-facing notices and guidance approved.
- [ ] Pilot acceptance tests passed.
- [ ] Operational owner and budget confirmed.

## 10. Deferred platform choice

The choice between self-managed PostgreSQL, a managed PostgreSQL provider, Supabase, Firebase-based services or another arrangement belongs in a separate platform evaluation. PostgreSQL is approved; the hosting and application platform are not.
