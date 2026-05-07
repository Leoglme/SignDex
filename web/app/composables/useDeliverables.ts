import { appDataDir, join } from '@tauri-apps/api/path'
import { readDir, writeFile, readFile, mkdir, exists } from '@tauri-apps/plugin-fs'

export type DeliverableIndexItem = {
  clientId: number
  clientName: string
  createdAtIso: string
  zipPath: string
  /**
   * Configuration du ZIP : permet de régénérer le même livrable plus tard.
   * Absent sur les anciennes entrées (rétrocompat).
   */
  variants?: {
    template_key: string
    swap_colors: boolean
    logo_slot: string
    photo1_slot: string
    photo2_slot: string
    show_side_photo?: boolean
  }[]
}

const INDEX_FILENAME = 'deliverables-index.json'

export async function getDeliverablesRootDir() {
  const root = await appDataDir()
  // Toujours utiliser `join` : `appDataDir` n’a pas de séparateur final garanti (sinon
  // `...fr.dibodev.signdex` + `signdex-...` → chemin invalide hors scope Tauri).
  return join(root, 'signdex-deliverables')
}

export async function ensureDeliverablesRoot() {
  const dir = await getDeliverablesRootDir()
  if (!(await exists(dir))) {
    await mkdir(dir, { recursive: true })
  }
  return dir
}

async function indexPath() {
  const dir = await ensureDeliverablesRoot()
  return join(dir, INDEX_FILENAME)
}

export async function readDeliverablesIndex(): Promise<DeliverableIndexItem[]> {
  const p = await indexPath()
  if (!(await exists(p))) return []
  const bytes = await readFile(p)
  const txt = new TextDecoder().decode(bytes)
  try {
    return JSON.parse(txt) as DeliverableIndexItem[]
  } catch {
    return []
  }
}

export async function appendDeliverableIndex(item: DeliverableIndexItem) {
  const p = await indexPath()
  const items = await readDeliverablesIndex()
  items.unshift(item)
  const txt = JSON.stringify(items.slice(0, 200), null, 2)
  await writeFile(p, new TextEncoder().encode(txt))
}

export async function listDeliverableFiles() {
  const dir = await ensureDeliverablesRoot()
  return await readDir(dir)
}

