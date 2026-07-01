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
  getProviders,
  getSystemInfo,
  listCheckpoints,
  listProviderKeys,
  setProviderKey,
  type Checkpoint,
  type ProviderKeyStatus,
  type ProviderStatus,
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
