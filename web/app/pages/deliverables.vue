<script setup lang="ts">
import { open } from '@tauri-apps/plugin-shell'
import { join } from '@tauri-apps/api/path'
import { readFile, writeFile } from '@tauri-apps/plugin-fs'
import { open as openDialog } from '@tauri-apps/plugin-dialog'
import JSZip from 'jszip'
import { appendDeliverableIndex, ensureDeliverablesRoot, readDeliverablesIndex, type DeliverableIndexItem } from '~/composables/useDeliverables'
import { IMAGE_SLOT_SELECT_ITEMS, type ImageSlotSource } from '~/constants/imageSlots'

const items = ref<DeliverableIndexItem[]>([])
const error = ref<string | null>(null)
const generating = ref<string | null>(null)
const attaching = ref<string | null>(null)

type VariantDraft = {
  template_key: string
  swap_colors: boolean
  logo_slot: ImageSlotSource
  photo1_slot: ImageSlotSource
  photo2_slot: ImageSlotSource
  show_side_photo: boolean
}

const attachModalOpen = ref(false)
const attachTarget = ref<DeliverableIndexItem | null>(null)
const attachZipPath = ref('')
const attachVariants = ref<VariantDraft[]>([])
const templates = ref<{ key: string; title: string; filename: string }[]>([])

function toFileUrl(p: string) {
  // Important: sur Windows, `shell.open('file:///...')` échoue si on percent-encode les accents
  // (Explorer interprète `%C3...` comme des caractères littéraux). On encode uniquement les espaces.
  const norm = (p || '').replaceAll('\\', '/')
  const safe = norm.replaceAll(' ', '%20')
  if (/^[a-zA-Z]:\//.test(safe)) return `file:///${safe}`
  if (safe.startsWith('/')) return `file://${safe}`
  return safe
}

async function ensureTemplatesLoaded() {
  if (templates.value.length) return
  templates.value = await apiFetch(`/templates`)
}

function _stemFromHtmlPath(p: string) {
  // HTML/foo_bar.html -> foo_bar
  const last = p.split('/').pop() || ''
  return last.endsWith('.html') ? last.slice(0, -5) : last
}

function detectTemplateKeyFromStem(stem: string, knownKeys: string[]) {
  // stem = slug_signature-v2 或 slug_signature-v2_variant-2
  for (const k of knownKeys) {
    if (stem.endsWith(`_${k}`)) return k
    if (stem.includes(`_${k}_variant-`)) return k
  }
  return null
}

function makeDefaultVariant(template_key: string): VariantDraft {
  return {
    template_key,
    swap_colors: false,
    logo_slot: 'default',
    photo1_slot: 'default',
    photo2_slot: 'default',
    show_side_photo: true,
  }
}

async function openAttachFromZip(it: DeliverableIndexItem) {
  attaching.value = it.zipPath
  error.value = null
  try {
    await ensureTemplatesLoaded()
    const knownKeys = templates.value.map((t) => t.key)

    const picked = await openDialog({
      multiple: false,
      directory: false,
      title: 'Choisir un ZIP SignDex',
      filters: [{ name: 'ZIP', extensions: ['zip'] }],
    })
    const zipPath = typeof picked === 'string' ? picked : picked?.path
    if (!zipPath) return

    const bytes = await readFile(zipPath)
    const zip = await JSZip.loadAsync(bytes)

    const htmlPaths = Object.keys(zip.files)
      .filter((p) => p.startsWith('HTML/') && p.endsWith('.html') && !zip.files[p].dir)
      .sort((a, b) => a.localeCompare(b))

    const keys: string[] = []
    for (const p of htmlPaths) {
      const stem = _stemFromHtmlPath(p)
      const k = detectTemplateKeyFromStem(stem, knownKeys)
      if (k) keys.push(k)
    }

    // fallback: si rien détecté, on laisse vide et l’utilisateur choisit à la main.
    attachTarget.value = it
    attachZipPath.value = zipPath
    attachVariants.value = keys.length ? keys.map((k) => makeDefaultVariant(k)) : []
    attachModalOpen.value = true
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    attaching.value = null
  }
}

async function attachAndRegenerate() {
  const it = attachTarget.value
  if (!it) return
  if (!attachVariants.value.length) {
    error.value = 'Aucune variante détectée. Ajoute au moins un template.'
    return
  }
  generating.value = it.zipPath
  error.value = null
  try {
    const variants = attachVariants.value.map((v) => ({
      template_key: v.template_key,
      swap_colors: v.swap_colors,
      logo_slot: v.logo_slot,
      photo1_slot: v.photo1_slot,
      photo2_slot: v.photo2_slot,
      show_side_photo: v.show_side_photo ?? true,
    }))

    const client = await apiFetch<{ id: number; name: string }>(`/clients/${it.clientId}`)
    const base = useApiBase()
    const service = it.service || 'signatures'
    const url =
      service === 'signatures' ? `${base}/clients/${it.clientId}/deliverable` : `${base}/services/${service}/clients/${it.clientId}/deliverable`
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ variants }),
    })
    if (!res.ok) throw new Error(await res.text())

    const blob = await res.blob()
    const bytes = new Uint8Array(await blob.arrayBuffer())

    const root = await ensureDeliverablesRoot()
    const ts = new Date().toISOString().replaceAll(':', '-')
    const safeName = client.name.replaceAll(' ', '_')
    const filename = `signdex_${service}_${safeName}_${ts}.zip`
    const filePath = await join(root, filename)
    await writeFile(filePath, bytes)

    await appendDeliverableIndex({
      service,
      clientId: it.clientId,
      clientName: client.name,
      createdAtIso: new Date().toISOString(),
      zipPath: filePath,
      variants,
    })

    attachModalOpen.value = false
    attachTarget.value = null
    attachZipPath.value = ''
    attachVariants.value = []

    await open(toFileUrl(filePath))
    await refresh()
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    generating.value = null
  }
}

async function refresh() {
  error.value = null
  try {
    items.value = await readDeliverablesIndex()
  } catch (e: any) {
    error.value = e?.message || String(e)
  }
}

async function regenerate(it: DeliverableIndexItem) {
  if (!it.variants?.length) return
  generating.value = it.zipPath
  error.value = null
  try {
    // Nom à jour (si l’utilisateur a modifié la fiche client après livraison).
    const client = await apiFetch<{ id: number; name: string }>(`/clients/${it.clientId}`)
    const base = useApiBase()
    const service = it.service || 'signatures'
    const url =
      service === 'signatures' ? `${base}/clients/${it.clientId}/deliverable` : `${base}/services/${service}/clients/${it.clientId}/deliverable`
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ variants: it.variants }),
    })
    if (!res.ok) throw new Error(await res.text())

    const blob = await res.blob()
    const bytes = new Uint8Array(await blob.arrayBuffer())

    const root = await ensureDeliverablesRoot()
    const ts = new Date().toISOString().replaceAll(':', '-')
    const safeName = client.name.replaceAll(' ', '_')
    const filename = `signdex_${service}_${safeName}_${ts}.zip`
    const filePath = await join(root, filename)
    await writeFile(filePath, bytes)

    await appendDeliverableIndex({
      service,
      clientId: it.clientId,
      clientName: client.name,
      createdAtIso: new Date().toISOString(),
      zipPath: filePath,
      variants: it.variants,
    })

    await open(toFileUrl(filePath))
    await refresh()
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    generating.value = null
  }
}

await refresh()
</script>

<template>
  <UDashboardPanel id="deliverables">
    <template #header>
      <UDashboardNavbar title="Livrables">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <UButton icon="i-lucide-refresh-cw" color="neutral" variant="ghost" @click="refresh" />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="space-y-4 p-4 sm:p-6">
        <UAlert v-if="error" color="red" variant="soft" title="Erreur" :description="error" />

        <UCard v-if="items.length === 0">
          <div class="text-muted text-sm">
            Aucun livrable pour l’instant. Va sur un client puis “Télécharger le livrable (ZIP)”.
          </div>
        </UCard>

        <div v-else class="space-y-3">
          <UCard v-for="it in items" :key="it.zipPath">
            <template #header>
              <div class="flex items-center justify-between gap-3">
                <div class="min-w-0">
                  <div class="truncate font-semibold">{{ it.clientName }}</div>
                  <div class="text-muted truncate text-sm">{{ new Date(it.createdAtIso).toLocaleString() }}</div>
                </div>
                <div class="flex items-center gap-2">
                  <UButton variant="soft" @click="open(toFileUrl(it.zipPath))">Ouvrir</UButton>
                  <UButton
                    color="primary"
                    variant="soft"
                    :disabled="!it.variants?.length"
                    :loading="generating === it.zipPath"
                    @click="regenerate(it)"
                  >
                    Régénérer
                  </UButton>
                  <UButton
                    v-if="!it.variants?.length"
                    color="neutral"
                    variant="soft"
                    :loading="attaching === it.zipPath"
                    @click="openAttachFromZip(it)"
                  >
                    Attacher depuis ZIP
                  </UButton>
                </div>
              </div>
            </template>
            <div class="text-muted break-all text-xs">{{ it.zipPath }}</div>
            <div v-if="!it.variants?.length" class="text-muted mt-2 text-xs">
              Ancien livrable : la configuration n’a pas été enregistrée, impossible de régénérer automatiquement.
            </div>
          </UCard>
        </div>
      </div>
    </template>
  </UDashboardPanel>

  <UModal
    v-model:open="attachModalOpen"
    title="Attacher une configuration"
    :description="attachZipPath ? `ZIP source : ${attachZipPath}` : 'Choisis un ZIP SignDex pour détecter les templates.'"
    class="sm:max-w-3xl"
  >
    <template #body>
      <div class="space-y-4">
        <UAlert
          v-if="attachVariants.length === 0"
          color="amber"
          variant="soft"
          title="Aucune variante détectée"
          description="Le ZIP n’a pas permis de déduire les templates. Ajoute une variante manuellement ci-dessous."
        />

        <div class="space-y-3">
          <div
            v-for="(v, idx) in attachVariants"
            :key="`${v.template_key}-${idx}`"
            class="ring-default grid gap-3 rounded-lg p-3 ring-1 sm:grid-cols-2"
          >
            <UFormField label="Template">
              <USelect
                v-model="v.template_key"
                class="w-full"
                :items="templates.map((t) => ({ label: t.title, value: t.key }))"
                :ui="{ content: 'z-[350] max-h-72' }"
              />
            </UFormField>

            <div class="flex flex-wrap items-center gap-x-4 gap-y-2 pt-6">
              <UCheckbox v-model="v.swap_colors" label="Échanger couleurs 1 ↔ 2" />
              <UCheckbox
                v-if="v.template_key === 'signature-v2'"
                v-model="v.show_side_photo"
                label="Afficher la vignette à droite"
              />
            </div>

            <UFormField label="Logo affiché">
              <USelect v-model="v.logo_slot" class="w-full" :items="IMAGE_SLOT_SELECT_ITEMS" :ui="{ content: 'z-[350]' }" />
            </UFormField>
            <UFormField label="Photo 1 affichée">
              <USelect
                v-model="v.photo1_slot"
                class="w-full"
                :items="IMAGE_SLOT_SELECT_ITEMS"
                :ui="{ content: 'z-[350]' }"
              />
            </UFormField>
            <UFormField label="Photo 2 affichée">
              <USelect
                v-model="v.photo2_slot"
                class="w-full"
                :items="IMAGE_SLOT_SELECT_ITEMS"
                :ui="{ content: 'z-[350]' }"
              />
            </UFormField>

            <div class="flex justify-end pt-6">
              <UButton
                color="red"
                variant="soft"
                icon="i-lucide-trash-2"
                @click="attachVariants.splice(idx, 1)"
              >
                Retirer
              </UButton>
            </div>
          </div>
        </div>

        <div class="flex flex-wrap gap-2">
          <UButton
            color="neutral"
            variant="soft"
            icon="i-lucide-plus"
            :disabled="templates.length === 0"
            @click="attachVariants.push(makeDefaultVariant(templates[0]?.key || ''))"
          >
            Ajouter une variante
          </UButton>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton color="neutral" variant="ghost" @click="attachModalOpen = false">Annuler</UButton>
        <UButton color="primary" variant="solid" :loading="!!generating" @click="attachAndRegenerate">
          Régénérer le livrable
        </UButton>
      </div>
    </template>
  </UModal>
</template>

