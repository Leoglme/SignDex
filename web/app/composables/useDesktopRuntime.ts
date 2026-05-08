/**
 * Détecte l’exécution dans le desktop Tauri vs navigateur — safe SSR, client-only.
 */
export function useDesktopRuntime() {
  const isDesktopApp = computed(() => {
    if (!import.meta.client) {
      return false
    }
    const w = window as Window & {
      __TAURI__?: unknown
      __TAURI_INTERNALS__?: unknown
    }
    return Boolean(w.__TAURI__ || w.__TAURI_INTERNALS__)
  })

  return { isDesktopApp }
}
