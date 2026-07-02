/**
 * System / runtime introspection API calls. Uses the shared `@/lib/api/client`
 * axios instance (baseURL '/api'). Powers the Integrations + Billing-adjacent
 * "runtime status" views. Both endpoints are read-only.
 */
import { api } from '@/lib/api/client'
import type { ProviderKey } from '@/types'

/** Per-provider configured flags (true when the backend has an API key for it). */
export type ProviderStatus = Record<ProviderKey, boolean>

/**
 * SystemInfo — the wire shape of GET /system/info. camelCase, mirroring the
 * backend settings/runtime summary. `providers` is the same flag map returned
 * by GET /system/providers.
 */
export interface SystemInfo {
  appName: string
  version: string
  env: string
  agents: number
  authEnabled: boolean
  rateLimitEnabled: boolean
  securityHeaders: boolean
  supabaseConfigured: boolean
  maxRecursion: number
  providers: ProviderStatus
}

/** Runtime + config summary. GET /system/info. */
export async function getSystemInfo(): Promise<SystemInfo> {
  const { data } = await api.get<SystemInfo>('/system/info')
  return data
}

/** Per-provider configured flags. GET /system/providers. */
export async function getProviders(): Promise<ProviderStatus> {
  const { data } = await api.get<ProviderStatus>('/system/providers')
  return data
}

/**
 * ProviderKeyStatus — the wire shape of one row from GET /system/provider-keys. Reports where
 * the ACTIVE key comes from (`source`) and, for a user-entered key, a masked hint (`masked`).
 * Raw key values are NEVER returned by the API.
 */
export interface ProviderKeyStatus {
  id: string
  label: string
  category: 'llm' | 'media'
  envVar: string
  docUrl: string
  /** A key is present in backend/.env for this provider. */
  envSet: boolean
  /** A key was saved in-app (stored under workspace/.state). */
  storedSet: boolean
  /** Which key is actually used: stored overrides env. */
  source: 'stored' | 'env' | 'none'
  configured: boolean
  /** Masked hint of the STORED key (e.g. "sk-o…wxyz"); null when none is stored. */
  masked: string | null
}

/** Per-provider key status (env / stored / none + masked). GET /system/provider-keys. */
export async function listProviderKeys(): Promise<ProviderKeyStatus[]> {
  const { data } = await api.get<ProviderKeyStatus[]>('/system/provider-keys')
  return data
}

/** Store (or replace) a provider key. PUT /system/provider-keys/{id}. Returns the new status. */
export async function setProviderKey(id: string, value: string): Promise<ProviderKeyStatus> {
  const { data } = await api.put<ProviderKeyStatus>(`/system/provider-keys/${id}`, { value })
  return data
}

/** Remove a stored provider key (falls back to env). DELETE /system/provider-keys/{id}. */
export async function clearProviderKey(id: string): Promise<ProviderKeyStatus> {
  const { data } = await api.delete<ProviderKeyStatus>(`/system/provider-keys/${id}`)
  return data
}

/** One credential field within a social publishing connector. Never carries a raw value. */
export interface SocialConnectorField {
  key: string
  label: string
  envVar: string
  secret: boolean
  required: boolean
  placeholder: string
  envSet: boolean
  storedSet: boolean
  source: 'stored' | 'env' | 'none'
  masked: string | null
}

/** A social publishing platform's connection status (multi-field). GET /system/social-connectors. */
export interface SocialConnector {
  id: string
  label: string
  docUrl: string
  /** Whether the REAL publish path is wired for this platform yet (else config-only). */
  publishSupported: boolean
  /** A caveat to surface (e.g. Instagram's public-URL requirement); may be empty. */
  note: string
  kinds: string[]
  /** True when every required field is present (stored or env). */
  configured: boolean
  fields: SocialConnectorField[]
}

/** Per-platform publishing-credential status. GET /system/social-connectors. */
export async function listSocialConnectors(): Promise<SocialConnector[]> {
  const { data } = await api.get<SocialConnector[]>('/system/social-connectors')
  return data
}

/** Set/clear a connector's fields (a value of '' clears that field). PUT /system/social-connectors/{id}. */
export async function setSocialConnector(
  id: string,
  values: Record<string, string>,
): Promise<SocialConnector> {
  const { data } = await api.put<SocialConnector>(`/system/social-connectors/${id}`, { values })
  return data
}

/** Remove every stored credential for a connector. DELETE /system/social-connectors/{id}. */
export async function clearSocialConnector(id: string): Promise<SocialConnector> {
  const { data } = await api.delete<SocialConnector>(`/system/social-connectors/${id}`)
  return data
}

/**
 * Checkpoint — one node in the cp-NNNN checkpoint lineage (GET /system/checkpoints).
 * `phase` is the build phase number (null for non-phase checkpoints); `phaseTitle`
 * is its human label; `status` is the lifecycle string (e.g. "committed"); `parent`
 * is the id of the checkpoint it descends from (null for the root).
 */
export interface Checkpoint {
  id: string
  phase: number | null
  phaseTitle: string
  status: string
  createdAt: string
  parent: string | null
}

/** The checkpoint lineage, oldest → newest. GET /system/checkpoints. */
export async function listCheckpoints(): Promise<Checkpoint[]> {
  const { data } = await api.get<Checkpoint[]>('/system/checkpoints')
  return data
}
