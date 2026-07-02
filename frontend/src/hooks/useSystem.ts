/**
 * System introspection hooks.
 *  - useSystemInfo(): the runtime + config summary (GET /system/info).
 *  - useProviders(): per-provider configured flags (GET /system/providers).
 * Both fail gracefully offline (jsdom/tests) — consumers default to undefined
 * and render an idle/"not configured" state rather than crashing.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  clearProviderKey,
  clearSocialConnector,
  getProviders,
  getSystemInfo,
  listCheckpoints,
  listProviderKeys,
  listSocialConnectors,
  setProviderKey,
  setSocialConnector,
  type Checkpoint,
  type ProviderKeyStatus,
  type ProviderStatus,
  type SocialConnector,
  type SystemInfo,
} from '@/lib/api/system'

/** Runtime + config summary — one retry so an offline host settles quickly. */
export function useSystemInfo() {
  return useQuery<SystemInfo>({
    queryKey: ['system', 'info'],
    queryFn: getSystemInfo,
    retry: 1,
  })
}

/** Per-provider configured flags — one retry so an offline host settles quickly. */
export function useProviders() {
  return useQuery<ProviderStatus>({
    queryKey: ['system', 'providers'],
    queryFn: getProviders,
    retry: 1,
  })
}

/** The cp-NNNN checkpoint lineage — one retry so an offline host settles quickly. */
export function useCheckpoints() {
  return useQuery<Checkpoint[]>({
    queryKey: ['system', 'checkpoints'],
    queryFn: listCheckpoints,
    retry: 1,
  })
}

/** Per-provider API-key status (env / stored / none + masked hint). GET /system/provider-keys. */
export function useProviderKeys() {
  return useQuery<ProviderKeyStatus[]>({
    queryKey: ['system', 'provider-keys'],
    queryFn: listProviderKeys,
    retry: 1,
  })
}

/** Invalidate every query whose "configured" state a key change can move. */
function useInvalidateProviderState() {
  const qc = useQueryClient()
  return () => {
    qc.invalidateQueries({ queryKey: ['system', 'provider-keys'] })
    qc.invalidateQueries({ queryKey: ['system', 'providers'] })
    qc.invalidateQueries({ queryKey: ['system', 'info'] })
  }
}

/** Save a provider key. On success refreshes the key + provider status queries. */
export function useSaveProviderKey() {
  const invalidate = useInvalidateProviderState()
  return useMutation<ProviderKeyStatus, Error, { id: string; value: string }>({
    mutationFn: ({ id, value }) => setProviderKey(id, value),
    onSuccess: invalidate,
  })
}

/** Remove a stored provider key. On success refreshes the key + provider status queries. */
export function useClearProviderKey() {
  const invalidate = useInvalidateProviderState()
  return useMutation<ProviderKeyStatus, Error, string>({
    mutationFn: (id) => clearProviderKey(id),
    onSuccess: invalidate,
  })
}

/** Per-platform social publishing credential status. GET /system/social-connectors. */
export function useSocialConnectors() {
  return useQuery<SocialConnector[]>({
    queryKey: ['system', 'social-connectors'],
    queryFn: listSocialConnectors,
    retry: 1,
  })
}

/** Save a social connector's fields. On success refreshes the connectors query. */
export function useSaveSocialConnector() {
  const qc = useQueryClient()
  return useMutation<SocialConnector, Error, { id: string; values: Record<string, string> }>({
    mutationFn: ({ id, values }) => setSocialConnector(id, values),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['system', 'social-connectors'] }),
  })
}

/** Disconnect a social connector (clear all its credentials). */
export function useClearSocialConnector() {
  const qc = useQueryClient()
  return useMutation<SocialConnector, Error, string>({
    mutationFn: (id) => clearSocialConnector(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['system', 'social-connectors'] }),
  })
}
