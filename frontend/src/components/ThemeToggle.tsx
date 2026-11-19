import { useState } from 'react';

/** Shared light/dark switch. The boot script in index.html sets the initial theme. */
export function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.dataset.theme === 'dark');

  function toggle() {
    const next = dark ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem('ecowatch-theme', next);
    } catch {
      // Storage can be blocked; the choice still applies for this visit.
    }
    setDark(next === 'dark');
  }

  return (
    <button
      type="button"
      className="theme-toggle"
      role="switch"
      aria-checked={dark}
      aria-label="Dark mode"
      title="Dark mode"
      onClick={toggle}
    >
      <span className="theme-toggle-thumb" aria-hidden="true" />
    </button>
  );
}
