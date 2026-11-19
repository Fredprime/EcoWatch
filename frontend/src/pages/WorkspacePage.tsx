import type { ReactNode } from 'react';

interface Props {
  title: string;
  description: string;
  children?: ReactNode;
}

export function WorkspacePage({ title, description, children }: Props) {
  return (
    <section>
      <header className="page-header">
        <h1>{title}</h1>
        <p>{description}</p>
      </header>
      {children ?? (
        <div className="card">
          <p className="muted">No content is available for this workspace. Content, permissions, and data shown here must remain role-scoped and evidence-grounded.</p>
        </div>
      )}
    </section>
  );
}
