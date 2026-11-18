import { WorkspacePage } from './WorkspacePage';

export function OverviewPage() {
  return (
    <WorkspacePage
      title="Overview"
      description="Active cases, recent observations, assigned work and system notices. This view is role-scoped in the full product."
    >
      <div className="grid grid-3">
        <div className="card"><h3>Recent observations</h3><p className="muted">No records loaded. Submitted observations will appear here after server receipt and within permitted scope.</p></div>
        <div className="card"><h3>Active cases</h3><p className="muted">Case summaries, owners and status will be shown to authorised users.</p></div>
        <div className="card"><h3>Notices</h3><p className="muted">System, review and assignment notices appear here. Machine-generated content must be labelled distinctly.</p></div>
      </div>
      <div className="card notice notice-info" role="note">
        <strong>Design baseline:</strong> EcoWatch follows Collect → Analyse → Prioritise → Intervene → Verify. This frontend scaffold reflects documented workspaces and states; data, integrations and approvals are not yet implemented.
      </div>
    </WorkspacePage>
  );
}
