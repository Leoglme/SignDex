<script setup lang="ts">
import { join } from '@tauri-apps/api/path'
import { writeFile } from '@tauri-apps/plugin-fs'
import { appendDeliverableIndex, ensureDeliverablesRoot } from '~/composables/useDeliverables'
import { editorGridColCardUi, editorLivrableCardUi } from '~/constants/editorCardUi'
import { IMAGE_SLOT_SELECT_ITEMS, type ImageSlotSource } from '~/constants/imageSlots'

type Client = { id: number; name: string; color_primary: string | null; color_secondary: string | null }
type Template = { key: string; title: string; filename: string }

type VariantRow = {
  id: string
  template_key: string
  swap_colors: boolean
  logo_slot: ImageSlotSource
  photo1_slot: ImageSlotSource
  photo2_slot: ImageSlotSource
  color_primary: string
  color_secondary: string
}

const SERVICE_KEY = 'cards-fidelite'
const SERVICE_TITLE = 'Cartes de fidélité'

const clients = ref<Client[]>([])
const templates = ref<Template[]>([])
const selectedClientId = ref<number | null>(null)

const deliverableVariants = ref<VariantRow[]>([])
const draftVariant = reactive({
  template_key: '',
  swap_colors: false,
  logo_slot: 'default' as ImageSlotSource,
  photo1_slot: 'default' as ImageSlotSource,
  photo2_slot: 'default' as ImageSlotSource,
  color_primary: '',
  color_secondary: '',
})

const previewIframeSrc = ref<string | null>(null)
const previewLoading = ref(false)
let previewSeq = 0
let previewDebounce: ReturnType<typeof setTimeout> | null = null

const loading = ref(true)
const error = ref<string | null>(null)
const generating = ref(false)
const deliverablePathModalOpen = ref(false)
const savedZipPath = ref('')

function syncVariantsWithTemplates() {
  const keys = new Set(templates.value.map((t) => t.key))
  deliverableVariants.value = deliverableVariants.value.filter((r) => keys.has(r.template_key))
  const first = templates.value[0]?.key ?? ''
  if (first && !keys.has(draftVariant.template_key)) {
    draftVariant.template_key = first
  }
}

function templateTitle(key: string) {
  return templates.value.find((t) => t.key === key)?.title ?? key
}

const templateSelectItems = computed(() => templates.value.map((t) => ({ label: t.title, value: t.key })))

function schedulePreview() {
  if (previewDebounce) clearTimeout(previewDebounce)
  previewDebounce = setTimeout(() => {
    previewDebounce = null
    loadPreview()
  }, 200)
}

async function loadPreview() {
  const templateKey = draftVariant.template_key || templates.value[0]?.key
  if (!templateKey) {
    const prev = previewIframeSrc.value
    previewIframeSrc.value = null
    if (prev) URL.revokeObjectURL(prev)
    return
  }

  const cid = selectedClientId.value
  const seq = ++previewSeq
  if (!cid) {
    previewLoading.value = false
    const prev = previewIframeSrc.value
    previewIframeSrc.value = null
    if (prev) URL.revokeObjectURL(prev)
    return
  }

  previewLoading.value = true
  try {
    const base = useApiBase()
    const body = {
      template_key: templateKey,
      client_id: cid,
      swap_colors: draftVariant.swap_colors,
      logo_slot: draftVariant.logo_slot,
      photo1_slot: draftVariant.photo1_slot,
      photo2_slot: draftVariant.photo2_slot,
      color_primary: draftVariant.color_primary || null,
      color_secondary: draftVariant.color_secondary || null,
    }
    const res = await fetch(`${base}/services/${SERVICE_KEY}/render/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(await res.text())
    const html = await res.text()
    if (seq !== previewSeq) return
    const old = previewIframeSrc.value
    previewIframeSrc.value = URL.createObjectURL(new Blob([html], { type: 'text/html;charset=utf-8' }))
    if (old) URL.revokeObjectURL(old)
  } catch (e: any) {
    if (seq === previewSeq) error.value = e?.message || String(e)
  } finally {
    if (seq === previewSeq) previewLoading.value = false
  }
}

const selectedClient = computed(() => clients.value.find((c) => c.id === selectedClientId.value) ?? null)

/** À chaque changement de client : on (re)remplit les couleurs draft avec celles du client (ou vide). */
watch(
  selectedClient,
  (c) => {
    draftVariant.color_primary = c?.color_primary || ''
    draftVariant.color_secondary = c?.color_secondary || ''
  },
  { immediate: true },
)

watch(selectedClientId, () => schedulePreview())
watch(draftVariant, () => schedulePreview(), { deep: true })

onMounted(() => schedulePreview())
onBeforeUnmount(() => {
  if (previewDebounce) clearTimeout(previewDebounce)
  const src = previewIframeSrc.value
  if (src) URL.revokeObjectURL(src)
})

async function refresh() {
  loading.value = true
  error.value = null
  try {
    clients.value = await apiFetch<Client[]>('/clients')
    templates.value = await apiFetch<Template[]>(`/services/${SERVICE_KEY}/templates`)
    syncVariantsWithTemplates()
    schedulePreview()
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

await refresh()

function pushDraftToDeliverable() {
  const k = draftVariant.template_key || templates.value[0]?.key
  if (!k) return
  deliverableVariants.value.push({
    id: crypto.randomUUID(),
    template_key: k,
    swap_colors: draftVariant.swap_colors,
    logo_slot: draftVariant.logo_slot,
    photo1_slot: draftVariant.photo1_slot,
    photo2_slot: draftVariant.photo2_slot,
    color_primary: draftVariant.color_primary,
    color_secondary: draftVariant.color_secondary,
  })
}

function removeVariant(rowId: string) {
  deliverableVariants.value = deliverableVariants.value.filter((r) => r.id !== rowId)
}

function duplicateVariant(row: VariantRow) {
  deliverableVariants.value.push({ ...row, id: crypto.randomUUID() })
}

function loadDraftFromRow(row: VariantRow) {
  draftVariant.template_key = row.template_key
  draftVariant.swap_colors = row.swap_colors
  draftVariant.logo_slot = row.logo_slot
  draftVariant.photo1_slot = row.photo1_slot
  draftVariant.photo2_slot = row.photo2_slot
  draftVariant.color_primary = row.color_primary
  draftVariant.color_secondary = row.color_secondary
  removeVariant(row.id)
}

function resetDeliverableList() {
  deliverableVariants.value = []
}

async function downloadDeliverable() {
  if (!selectedClientId.value || !selectedClient.value) return
  if (!deliverableVariants.value.length) {
    error.value = 'Ajoute au moins une variante au livrable.'
    return
  }
  generating.value = true
  error.value = null
  try {
    const base = useApiBase()
    const variants = deliverableVariants.value.map((v) => ({
      template_key: v.template_key,
      swap_colors: v.swap_colors,
      logo_slot: v.logo_slot,
      photo1_slot: v.photo1_slot,
      photo2_slot: v.photo2_slot,
      color_primary: v.color_primary || null,
      color_secondary: v.color_secondary || null,
    }))
    const res = await fetch(`${base}/services/${SERVICE_KEY}/clients/${selectedClientId.value}/deliverable`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ variants }),
    })
    if (!res.ok) throw new Error(await res.text())

    const blob = await res.blob()
    const bytes = new Uint8Array(await blob.arrayBuffer())

    const root = await ensureDeliverablesRoot()
    const ts = new Date().toISOString().replaceAll(':', '-')
    const safeName = selectedClient.value.name.replaceAll(' ', '_')
    const filename = `signdex_${SERVICE_KEY}_${safeName}_${ts}.zip`
    const filePath = await join(root, filename)
    await writeFile(filePath, bytes)

    await appendDeliverableIndex({
      service: SERVICE_KEY,
      clientId: selectedClient.value.id,
      clientName: selectedClient.value.name,
      createdAtIso: new Date().toISOString(),
      zipPath: filePath,
      variants,
    })

    savedZipPath.value = filePath
    deliverablePathModalOpen.value = true
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <UDashboardPanel :id="`service-${SERVICE_KEY}`">
    <template #header>
      <UDashboardNavbar :title="SERVICE_TITLE">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <div class="flex items-center gap-2">
            <UButton icon="i-lucide-download" color="primary" variant="solid" :loading="generating" :disabled="!selectedClientId" @click="downloadDeliverable">
              Télécharger le livrable
            </UButton>
            <UButton to="/deliverables" color="neutral" variant="ghost" icon="i-lucide-package" />
            <UButton icon="i-lucide-refresh-cw" color="neutral" variant="ghost" :loading="loading" @click="refresh" />
          </div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="space-y-4">
        <UAlert v-if="error" color="red" variant="soft" title="Erreur" :description="error" />

        <div class="min-w-0 space-y-4">
          <div class="grid min-w-0 items-stretch gap-4 xl:grid-cols-[minmax(18rem,22rem)_minmax(0,1fr)]">
            <UCard :ui="editorGridColCardUi">
              <template #header>
                <div class="font-semibold">Client</div>
              </template>

              <div class="min-w-0 space-y-3">
                <UFormField label="Données injectées dans le template" class="w-full min-w-0">
                  <USelect
                    v-model="selectedClientId"
                    class="w-full"
                    :items="[{ label: '— Sélectionne un client —', value: null }, ...clients.map((c) => ({ label: c.name, value: c.id }))]"
                    :ui="{
                      base: 'w-full',
                      content: 'z-[300] max-h-72 w-(--reka-select-trigger-width)',
                    }"
                  />
                </UFormField>
                <p class="text-muted text-xs leading-relaxed">Format carte de fidélité standard : 3,5"×2" (1050×600 @300dpi), imprimable VistaPrint. Recto = visuel + nom, verso = grille de tampons.</p>
              </div>
            </UCard>

            <UCard :ui="editorGridColCardUi">
              <template #header>
                <div class="font-semibold">Édition</div>
              </template>

              <UFormField label="Template" class="min-w-0">
                <USelect
                  v-model="draftVariant.template_key"
                  class="w-full"
                  :items="templateSelectItems"
                  placeholder="Template…"
                  :ui="{
                    base: 'w-full',
                    content: 'z-[300] max-h-72 w-(--reka-select-trigger-width)',
                  }"
                />
              </UFormField>
              <SignDexColorOverrideFields
                v-model:color1="draftVariant.color_primary"
                v-model:color2="draftVariant.color_secondary"
                :default-color1="selectedClient?.color_primary || null"
                :default-color2="selectedClient?.color_secondary || null"
                :disabled="!selectedClient"
              />
              <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
                <UCheckbox v-model="draftVariant.swap_colors" label="Échanger couleurs 1 ↔ 2" />
              </div>
              <div class="grid gap-3 sm:grid-cols-3">
                <UFormField label="Logo affiché">
                  <USelect v-model="draftVariant.logo_slot" class="w-full" :items="IMAGE_SLOT_SELECT_ITEMS" :ui="{ base: 'w-full', content: 'z-[300]' }" />
                </UFormField>
                <UFormField label="Photo 1 affichée">
                  <USelect v-model="draftVariant.photo1_slot" class="w-full" :items="IMAGE_SLOT_SELECT_ITEMS" :ui="{ base: 'w-full', content: 'z-[300]' }" />
                </UFormField>
                <UFormField label="Photo 2 affichée">
                  <USelect v-model="draftVariant.photo2_slot" class="w-full" :items="IMAGE_SLOT_SELECT_ITEMS" :ui="{ base: 'w-full', content: 'z-[300]' }" />
                </UFormField>
              </div>
              <div class="flex flex-wrap gap-2">
                <UButton color="primary" icon="i-lucide-plus" @click="pushDraftToDeliverable">Ajouter au livrable</UButton>
              </div>
            </UCard>
          </div>

          <UCard :ui="editorLivrableCardUi">
            <template #header>
              <div class="flex min-w-0 flex-col gap-3">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <div class="font-semibold">Livrable — aperçu</div>
                  <UButton size="xs" color="neutral" variant="soft" icon="i-lucide-rotate-ccw" @click="resetDeliverableList">
                    Tout réinitialiser
                  </UButton>
                </div>
                <p class="text-muted text-xs leading-relaxed">Liste des variantes et aperçu HTML selon la configuration dans Édition.</p>
              </div>
            </template>

            <div v-if="deliverableVariants.length" class="space-y-2">
              <div class="text-muted text-xs font-medium uppercase tracking-wide">Dans le livrable ({{ deliverableVariants.length }})</div>
              <ul class="flex flex-col gap-2">
                <li v-for="row in deliverableVariants" :key="row.id" class="ring-default flex flex-wrap items-center gap-2 rounded-lg px-3 py-2 ring-1">
                  <span class="min-w-0 flex-1 truncate text-sm font-medium">{{ templateTitle(row.template_key) }}</span>
                  <div class="flex shrink-0 gap-1">
                    <UButton size="xs" color="neutral" variant="ghost" icon="i-lucide-pencil" title="Charger dans l’éditeur" @click="loadDraftFromRow(row)" />
                    <UButton size="xs" color="neutral" variant="ghost" icon="i-lucide-copy" title="Dupliquer" @click="duplicateVariant(row)" />
                    <UButton size="xs" color="neutral" variant="ghost" icon="i-lucide-trash-2" title="Retirer" @click="removeVariant(row.id)" />
                  </div>
                </li>
              </ul>
            </div>
            <p v-else class="text-muted text-sm">Aucune variante dans le livrable pour l’instant.</p>

            <div class="text-muted mt-4 text-sm">
              Aperçu HTML — même configuration que dans Édition.
              <span v-if="previewLoading" class="text-primary ml-2">Mise à jour…</span>
            </div>

            <div class="ring-default relative mt-4 overflow-hidden rounded-lg ring-1">
              <iframe v-if="selectedClientId && previewIframeSrc" :src="previewIframeSrc" class="h-[min(70vh,760px)] min-h-[420px] w-full bg-white" referrerpolicy="no-referrer" />
              <div v-else class="text-muted p-4 text-sm">Sélectionne un client et un template pour l’aperçu.</div>
            </div>
          </UCard>
        </div>
      </div>
    </template>
  </UDashboardPanel>

  <SignDexDeliverablePathModal v-model:open="deliverablePathModalOpen" :path="savedZipPath" />
</template>
