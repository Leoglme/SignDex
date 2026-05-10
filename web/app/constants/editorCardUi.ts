/**
 * Cartes d’édition : gris très léger (un cran sous le blanc pur), lisible sur le fond du panel.
 */
const editorCardFill =
  'bg-zinc-50 ring-1 ring-zinc-200/80 dark:bg-zinc-900 dark:ring-zinc-600/55'

export const editorGridColCardUi = {
  root: `min-w-0 h-full flex flex-col rounded-lg ${editorCardFill} shadow-sm dark:shadow-md overflow-visible`,
  header: 'shrink-0 border-b border-default/50',
  body: 'flex-1 min-h-0 flex flex-col gap-4 overflow-visible',
}

/** Colonne « Modifier le client » : corps scrollable entre deux cartes à hauteur alignée. */
export const editorClientFormGridCardUi = {
  root: `min-w-0 h-full flex flex-col rounded-lg ${editorCardFill} shadow-sm dark:shadow-md`,
  header: 'shrink-0 border-b border-default/50',
  body: 'flex-1 min-h-0 flex flex-col overflow-hidden',
}

/** Carte « Livrable » pleine largeur (pas de h-full sur la grille). */
export const editorLivrableCardUi = {
  root: `min-w-0 rounded-lg ${editorCardFill} shadow-md dark:shadow-lg`,
  header: 'shrink-0 border-b border-default/50',
  body: 'min-w-0 flex flex-col gap-4',
}
