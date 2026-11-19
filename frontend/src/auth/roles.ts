/** Role codes mirror the backend `Role` enum in identity/permissions.py.
 *
 * UI gating here is convenience only: the server enforces every permission.
 * Roles come from the server on /auth/me; nothing is inferred or escalated here.
 */
import type { AuthMeResponse } from '../api/types';

export const SYSTEM_ADMIN_ROLE = 'system_admin';

export const CORRELATION_REVIEW_ROLES = [
  'reviewer',
  'investigator',
  'environmental_specialist',
  'organisation_admin',
  SYSTEM_ADMIN_ROLE,
] as const;

/** Effective roles from the platform role and active organisation memberships. */
export function rolesFor(me: AuthMeResponse | null): string[] {
  if (!me) return [];
  const roles = new Set<string>();
  if (me.systemRole === SYSTEM_ADMIN_ROLE) roles.add(SYSTEM_ADMIN_ROLE);
  for (const membership of me.memberships) {
    if (membership.isActive) roles.add(membership.role);
  }
  return [...roles];
}

/** `all` means any authenticated account; `me` is null until sign-in resolves. */
export function hasAnyRole(
  me: AuthMeResponse | null,
  allowed: readonly string[],
): boolean {
  if (!me) return false;
  if (allowed.includes('all')) return true;
  const held = rolesFor(me);
  return held.some((role) => allowed.includes(role));
}
