/**
 * System introspection hooks.
 *  - useSystemInfo(): the runtime + config summary (GET /system/info).
 *  - useProviders(): per-provider configured flags (GET /system/providers).
 * Both fail gracefully offline (jsdom/tests) — consumers default to undefined
 * and render an idle/"not configured" state rather than crashing.
 */
import { useQuery } from '@tanstack/react-query'
import {
  getProviders,
  getSystemInfo,
  listCheckpoints,
  type Checkpoint,
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
