export function useApiBase() {
  const config = useRuntimeConfig()
  return config.public.apiBase as string
}

/**
 * En-tête d'authentification (JWT stocké en cookie) pour les appels `fetch` bruts
 * — notamment les téléchargements binaires (ZIP) qui ne passent pas par `apiFetch`.
 */
export function authHeaders(): Record<string, string> {
  const token = useCookie<string | null>('signdex_token')
  return token.value ? { Authorization: `Bearer ${token.value}` } : {}
}

export async function apiFetch<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const base = useApiBase()
  const token = useCookie<string | null>('signdex_token')
  const headers: Record<string, string> = { ...((opts.headers as Record<string, string>) || {}) }
  if (token.value) {
    headers.Authorization = `Bearer ${token.value}`
  }
  const res = await fetch(`${base}${path}`, { ...opts, headers })
  if (!res.ok) {
    if (res.status === 401) {
      // Session invalide/expirée : on purge. La navigation suivante repasse par le middleware d'auth.
      token.value = null
      useState<unknown>('signdex_user').value = null
    }
    const txt = await res.text().catch(() => '')
    throw new Error(`API ${res.status}: ${txt || res.statusText}`)
  }
  if (res.status === 204) {
    return undefined as T
  }
  return (await res.json()) as T
}
