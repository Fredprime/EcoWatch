export function EmptyState({ title, detail }: { title: string; detail?: string }) {
  return (
    <div className="empty-state" role="status">
      <p><strong>{title}</strong></p>
      {detail && <p className="muted">{detail}</p>}
    </div>
  );
}
