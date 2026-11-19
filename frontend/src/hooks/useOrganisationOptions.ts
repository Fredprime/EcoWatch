import { useCallback } from 'react';
import { listOrganisations } from '../api/admin';
import { useAuth } from '../auth/authContext';
import { useApiResource } from './useApiResource';

export function useOrganisationOptions(authenticated: boolean) {
  const { me } = useAuth();
  const load = useCallback(() => listOrganisations(), []);
  const orgs = useApiResource(load, 'shared:organisations', authenticated);
  const options =
    orgs.state.status === 'success'
      ? orgs.state.data.items.map((org) => ({ value: org.id, label: org.name }))
      : (me?.memberships ?? []).map((m) => ({
          value: m.organisationId,
          label: m.organisationId,
        }));
  return {
    options,
    defaultOrgId: options[0]?.value ?? me?.memberships[0]?.organisationId ?? '',
  };
}
