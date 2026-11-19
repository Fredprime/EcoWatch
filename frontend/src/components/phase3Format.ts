/** Display a server timestamp without inventing a value when it is absent. */
export function formatTime(value: string | null | undefined): string {
  if (!value) return 'Not provided';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

/** Show recorded text or a clear absence marker; never fabricate a value. */
export function displayText(value: string | null | undefined, absent = 'Not recorded'): string {
  return value && value.trim() ? value : absent;
}
