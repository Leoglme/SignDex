export function useApiBase() {
  const config = useRuntimeConfig()
  return config.public.apiBase as string
}

export async function apiFetch<T>(path: string, opts: RequestInit = {}) {
  const base = useApiBase()
  const res = await fetch(`${base}${path}`, {
    ...opts,
    headers: {
      ...(opts.headers || {}),
    },
  })
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    throw new Error(`API ${res.status}: ${txt || res.statusText}`)
  }
  return (await res.json()) as T
}

