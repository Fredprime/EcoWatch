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

export const WORKSPACES: Workspace[] = [
  { id: 'overview', label: 'Overview', path: '/workspace', description: 'Recent observations and service status within your permitted scope.', roles: ['all'] },
  { id: 'evidence', label: 'Evidence Intelligence', path: '/evidence', description: 'Candidate relationships, duplicate review and evidence context.', roles: ['reviewer', 'investigator'] },
  { id: 'monitoring', label: 'Monitoring', path: '/monitoring', description: 'Maps, monitored areas, indicators and historical layers.', roles: ['specialist', 'investigator', 'reviewer'] },
  { id: 'cases', label: 'Cases', path: '/cases', description: 'Case summary, map, timeline, evidence and review history.', roles: ['investigator', 'reviewer', 'specialist'] },
  { id: 'analysis', label: 'Analysis', path: '/analysis', description: 'Datasets, methods, outputs and interpretation.', roles: ['specialist'] },
  { id: 'prioritisation', label: 'Prioritisation', path: '/prioritisation', description: 'Transparent factors and review decisions.', roles: ['investigator', 'manager'] },
  { id: 'interventions', label: 'Interventions', path: '/interventions', description: 'Approved actions, owners, milestones and records.', roles: ['manager', 'investigator'] },
  { id: 'verification', label: 'Verification', path: '/verification', description: 'Baselines, follow-up measurements and outcome assessments.', roles: ['specialist', 'manager'] },
  { id: 'admin', label: 'Administration', path: '/admin', description: 'Users, organisations, vocabularies, imports, audit and configuration.', roles: ['admin'] },
];
