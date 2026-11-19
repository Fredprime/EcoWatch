import type { ReactNode } from 'react';

type Variant = 'info' | 'warn' | 'danger' | 'neutral';

const variantClass: Record<Variant, string> = {
  info: 'notice notice-info',
  warn: 'notice notice-warn',
  danger: 'notice notice-danger',
  neutral: 'notice',
};

export function Notice({ title, children, variant = 'neutral', role }: { title?: string; children: ReactNode; variant?: Variant; role?: 'note' | 'alert' | 'status' }) {
  return (
    <div className={variantClass[variant]} role={role}>
      {title && <strong>{title} </strong>}
      {children}
    </div>
  );
}
