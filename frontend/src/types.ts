export type WorkspaceId =
  | 'overview'
  | 'evidence'
  | 'monitoring'
  | 'cases'
  | 'analysis'
  | 'prioritisation'
  | 'interventions'
  | 'verification'
  | 'admin';

export interface Workspace {
  id: WorkspaceId;
  label: string;
  path: string;
  description: string;
  roles: string[];
}

// Role codes match the backend Role enum; UI gating is convenience only.
const STAFF_ROLES = [
  'reviewer',
  'investigator',
  'environmental_specialist',
  'intervention_manager',
  'organisation_admin',
  'system_admin',
];

export const WORKSPACES: Workspace[] = [
  { id: 'overview', label: 'Overview', path: '/workspace', description: 'Recent observations and service status within your permitted scope.', roles: ['all'] },
  { id: 'evidence', label: 'Evidence Intelligence', path: '/evidence', description: 'Candidate relationships, duplicate review and evidence context.', roles: STAFF_ROLES },
  { id: 'monitoring', label: 'Monitoring', path: '/monitoring', description: 'Maps, monitored areas, indicators and historical layers.', roles: STAFF_ROLES },
  { id: 'cases', label: 'Cases', path: '/cases', description: 'Case summary, map, timeline, evidence and review history.', roles: STAFF_ROLES },
  { id: 'analysis', label: 'Analysis', path: '/analysis', description: 'Datasets, methods, outputs and interpretation.', roles: ['reviewer', 'investigator', 'environmental_specialist', 'organisation_admin', 'system_admin'] },
  { id: 'prioritisation', label: 'Prioritisation', path: '/prioritisation', description: 'Transparent factors and review decisions.', roles: ['investigator', 'environmental_specialist', 'organisation_admin', 'system_admin'] },
  { id: 'interventions', label: 'Interventions', path: '/interventions', description: 'Approved actions, owners, milestones and records.', roles: ['environmental_specialist', 'intervention_manager', 'organisation_admin', 'system_admin'] },
  { id: 'verification', label: 'Verification', path: '/verification', description: 'Baselines, follow-up measurements and outcome assessments.', roles: ['investigator', 'environmental_specialist', 'intervention_manager', 'organisation_admin', 'system_admin'] },
  { id: 'admin', label: 'Administration', path: '/admin', description: 'Users, organisations, vocabularies, imports, audit and configuration.', roles: ['organisation_admin', 'system_admin'] },
];
