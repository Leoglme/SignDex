import type { ComputedRef } from 'vue'
import type { HostBranding } from '~/types/auth'

/** Libellés d'hôtes qui ne correspondent à aucun client (app admin SignDex, dev local). */
const NON_CLIENT_LABELS = new Set(['', 'signdex', 'www', 'localhost', '127'])

/** Couleur de texte lisible (noir/blanc) selon la luminance d'une couleur hex. */
function contrastText(hex: string): string {
  const h = hex.replace('#', '')
  const full = h.length === 3 ? h.split('').map(c => c + c).join('') : h
  const r = Number.parseInt(full.slice(0, 2), 16)
  const g = Number.parseInt(full.slice(2, 4), 16)
  const b = Number.parseInt(full.slice(4, 6), 16)
  if ([r, g, b].some(Number.isNaN)) return '#ffffff'
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.6 ? '#111827' : '#ffffff'
}

/**
 * Branding déduit du sous-domaine (ex. `lexial.dibodev.fr` → couleurs LEXIAL), appliqué
 * AVANT connexion (page de login). L'admin peut prévisualiser via `?org=<slug>`.
 */
export function useHostBranding() {
  const branding = useState<HostBranding | null>('host_branding', () => null)

  /**
   * Charge le branding de l'hôte courant (SSR-safe, sans flash au chargement). Idempotent.
   * @returns le branding trouvé, ou `null` (hôte non-client → thème SignDex par défaut).
   */
  async function loadHostBranding(): Promise<HostBranding | null> {
    const route = useRoute()
    const override = (typeof route.query.org === 'string' ? route.query.org : '').trim().toLowerCase()
    const label = override || (useRequestURL().hostname.split('.')[0]?.toLowerCase() ?? '')
    if (NON_CLIENT_LABELS.has(label)) {
      branding.value = null
      return null
    }
    // Le branding est cosmétique : il ne doit JAMAIS bloquer le rendu du login.
    // Timeout court → si l'API est lente/injoignable, on retombe sur le thème par défaut.
    const { data } = await useAsyncData<HostBranding | null>(
      `host-branding:${label}`,
      () => apiFetch<HostBranding | null>(
        `/auth/branding?slug=${encodeURIComponent(label)}`,
        { signal: AbortSignal.timeout(2500) },
      ).catch(() => null),
    )
    branding.value = data.value
    return data.value
  }

  const brandColor: ComputedRef<string | null> = computed(() => branding.value?.brand_color || null)
  const brandLogoUrl: ComputedRef<string | null> = computed(() => branding.value?.brand_logo_url || null)
  const organizationName: ComputedRef<string | null> = computed(() => branding.value?.organization_name || null)

  /** Favicon = logo du client sur son sous-domaine, sinon le favicon SignDex par défaut. */
  const faviconHref: ComputedRef<string> = computed(() => branding.value?.brand_logo_url || '/favicon.ico')

  /** `:root{--ui-primary:…}` pour teinter les accents Nuxt UI (focus, liens…) à la couleur du client. */
  const brandCss: ComputedRef<string> = computed(() =>
    brandColor.value ? `:root{--ui-primary:${brandColor.value};}` : '',
  )

  /** Bouton « plein » à la couleur du client, texte noir/blanc auto lisible (clair ET sombre). */
  const brandButtonStyle: ComputedRef<Record<string, string>> = computed(() =>
    brandColor.value
      ? { backgroundColor: brandColor.value, borderColor: brandColor.value, color: contrastText(brandColor.value) }
      : {},
  )

  return { branding, loadHostBranding, brandColor, brandLogoUrl, organizationName, faviconHref, brandCss, brandButtonStyle }
}
