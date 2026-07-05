import type { ComputedRef } from 'vue'

/** Couleur de texte lisible (noir/blanc) selon la luminance d'une couleur hex. */
function contrastText(hex: string): string {
  const h = hex.replace('#', '')
  const full = h.length === 3 ? h.split('').map(c => c + c).join('') : h
  const r = Number.parseInt(full.slice(0, 2), 16)
  const g = Number.parseInt(full.slice(2, 4), 16)
  const b = Number.parseInt(full.slice(4, 6), 16)
  if ([r, g, b].some(Number.isNaN)) return '#ffffff'
  // Luminance perçue : sombre → texte blanc, clair → texte noir. Indépendant du thème.
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.6 ? '#111827' : '#ffffff'
}

/** Branding de l'organisation connectée : couleur primaire + style des boutons de marque. */
export function useBrand() {
  const { user } = useAuth()

  const brandColor: ComputedRef<string | null> = computed(() => user.value?.brand_color || null)

  /** Bouton « plein » à la couleur de l'orga, texte noir/blanc auto (lisible en clair ET en sombre). */
  const brandButtonStyle: ComputedRef<Record<string, string>> = computed(() =>
    brandColor.value
      ? { backgroundColor: brandColor.value, borderColor: brandColor.value, color: contrastText(brandColor.value) }
      : {},
  )

  /** Variables CSS pour teinter les accents Nuxt UI (lien actif…) à la couleur de l'orga. */
  const brandVars: ComputedRef<Record<string, string>> = computed(() =>
    brandColor.value ? { '--ui-primary': brandColor.value } : {},
  )

  return { brandColor, brandButtonStyle, brandVars }
}
