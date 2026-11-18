type Tone = 'draft' | 'queued' | 'submitted' | 'received' | 'review' | 'neutral';

const toneClass: Record<Tone, string> = {
  draft: 'status-draft',
  queued: 'status-queued',
  submitted: 'status-submitted',
  received: 'status-received',
  review: 'status-draft',
  neutral: 'status-draft',
};

export function StatusPill({ label, tone = 'neutral' }: { label: string; tone?: Tone }) {
  return <span className={`status-pill ${toneClass[tone]}`}>{label}</span>;
}
