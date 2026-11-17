# 18 — Deferred Platform Evaluation Brief: Supabase, Firebase and Alternatives

**Status:** Deferred. This document defines a future evaluation; it does not select a platform.

## 1. Why this is a separate evaluation

The project owner has approved PostgreSQL as the database technology but has asked that Supabase and Firebase be considered in a different document and not treated as a pilot priority.

The database decision and the application-platform decision are related but not identical. PostgreSQL is a relational database. Supabase and Firebase are broader platform offerings with different service models and architectural assumptions.

## 2. Questions the future evaluation must answer

- Does the platform use or require PostgreSQL?
- Can it support the required relational and geospatial data model?
- What authentication and role-management features are included?
- How are file uploads and access permissions handled?
- Can background processing and long-running geospatial tasks be supported?
- What are the limits, pricing model and likely growth costs?
- Where is data stored and backed up?
- How can data and files be exported?
- What vendor-specific dependencies are introduced?
- What security controls and audit capabilities are available?
- Can the team operate and troubleshoot it with its available skills?
- Does it support the pilot's connectivity and performance needs?

## 3. Candidate categories

### Supabase
Evaluate as a managed application platform built around PostgreSQL, including its database hosting, authentication, storage, APIs, access controls and pricing. Verify current product capabilities and limitations at the time of evaluation.

### Firebase
Evaluate as a broader application platform with its own data services and ecosystem. Assess whether its data model and services fit the project's PostgreSQL decision or would introduce a separate database architecture and data synchronisation burden.

### Other options
Consider managed PostgreSQL providers or self-managed PostgreSQL if appropriate. Include the cost of operational responsibility, backups, upgrades, security and monitoring—not just the advertised monthly price.

## 4. Evaluation method

1. Finalise pilot requirements.
2. Estimate users, submissions, media volume and analytical workloads.
3. Identify required database features and spatial queries.
4. Compare security, privacy, data location and governance.
5. Estimate total cost for realistic usage.
6. Test a small proof of concept only after design approval.
7. Test export and recovery.
8. Record trade-offs and recommendation.
9. Obtain project-owner approval.

## 5. Decision boundary

Until the evaluation is completed and approved:
- PostgreSQL remains the approved database technology.
- Supabase is not approved.
- Firebase is not approved.
- No assumption should be made that either will host the pilot.
- This deferred evaluation must not delay the current project documentation.
