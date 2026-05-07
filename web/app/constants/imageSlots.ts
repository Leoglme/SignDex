export type ImageSlotSource = 'default' | 'logo' | 'photo1' | 'photo2'

/** Quelle image de la fiche client remplit chaque emplacement du template. */
export const IMAGE_SLOT_SELECT_ITEMS: { label: string; value: ImageSlotSource }[] = [
  { label: 'Défaut (fiche client)', value: 'default' },
  { label: 'Logo', value: 'logo' },
  { label: 'Photo 1', value: 'photo1' },
  { label: 'Photo 2', value: 'photo2' },
]
