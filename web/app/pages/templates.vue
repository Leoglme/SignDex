<script setup lang="ts">
import { join } from '@tauri-apps/api/path'
import { writeFile } from '@tauri-apps/plugin-fs'
import { appendDeliverableIndex, ensureDeliverablesRoot } from '~/composables/useDeliverables'
import { editorGridColCardUi, editorLivrableCardUi } from '~/constants/editorCardUi'
import { IMAGE_SLOT_SELECT_ITEMS, type ImageSlotSource } from '~/constants/imageSlots'

type ClientListItem = { id: number; name: string; color_primary: string | null; color_secondary: string | null }
type ClientDetail = ClientListItem & { title?: string | null; subtitle?: string | null }
type Template = { key: string; title: string; filename: string }

type DeliverableVariantRow = {
  id: string
  template_key: string
  swap_colors: boolean
  logo_slot: ImageSlotSource
  photo1_slot: ImageSlotSource
  photo2_slot: ImageSlotSource
  show_side_photo: boolean
  show_right_logo: boolean
  show_notes: boolean
  color_primary: string
  color_secondary: string
  /** Figé à l’ajout au livrable (titre / sous-titre de l’éditeur). */
  title: string
  subtitle: string
}

const clients = ref<ClientListItem[]>([])
const selectedClientDetail = ref<ClientDetail | null>(null)
const signatureText = reactive({ title: '', subtitle: '' })
const templates = ref<Template[]>([])

const selectedClientId = ref<number | null>(null)

const deliverableVariants = ref<DeliverableVariantRow[]>([])
const draftVariant = reactive({
  template_key: '',
  swap_colors: false,
  logo_slot: 'default' as ImageSlotSource,
  photo1_slot: 'default' as ImageSlotSource,
  photo2_slot: 'default' as ImageSlotSource,
  show_side_photo: true,
  show_right_logo: true,
  show_notes: false,
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

const templateSelectItems = computed(() =>
  templates.value.map((t) => ({ label: t.title, value: t.key })),
)

const draftIsSignatureV2 = computed(() => draftVariant.template_key === 'signature-v2')
const draftUsesDualVisualLayout = computed(() => {
  const k = draftVariant.template_key
  return k === 'signature-v6' || k === 'signature-v8'
})
const draftShowsNotesOption = computed(() => {
  const k = draftVariant.template_key
  return k === 'signature-v1' || k === 'signature-v2'
})

function schedulePreview() {
  if (previewDebounce) clearTimeout(previewDebounce)
  previewDebounce = setTimeout(() => {
    previewDebounce = null
    loadPreview()
  }, 200)
}

/** Sans client : GET placeholder API. Avec client : POST preview (brouillon). */
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
      show_side_photo: draftVariant.show_side_photo,
      show_right_logo: draftVariant.show_right_logo,
      show_notes: draftVariant.show_notes,
      ...(signatureText.title.trim() ? { title: signatureText.title.trim() } : {}),
      ...(signatureText.subtitle.trim() ? { subtitle: signatureText.subtitle.trim() } : {}),
      color_primary: draftVariant.color_primary || null,
      color_secondary: draftVariant.color_secondary || null,
    }
    const res = await fetch(`${base}/render/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
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

const placeholderPreviewUrl = computed(() => {
  if (selectedClientId.value) return null
  const k = draftVariant.template_key || templates.value[0]?.key
  if (!k) return null
  const base = useApiBase()
  return `${base}/render/${k}.html`
})

const selectedClient = computed(() => clients.value.find((c) => c.id === selectedClientId.value) ?? null)

function syncSignatureTextFromClient(c: ClientDetail | null) {
  if (!c) {
    signatureText.title = ''
    signatureText.subtitle = ''
    return
  }
  signatureText.title = c.title?.trim() ?? ''
  signatureText.subtitle = c.subtitle?.trim() ?? ''
}

async function loadSelectedClientDetail(id: number | null) {
  if (!id) {
    selectedClientDetail.value = null
    syncSignatureTextFromClient(null)
    return
  }
  try {
    const c = await apiFetch<ClientDetail>(`/clients/${id}`)
    selectedClientDetail.value = c
    syncSignatureTextFromClient(c)
  } catch (e: any) {
    error.value = e?.message || String(e)
  }
}

/** À chaque changement de client : couleurs draft + fiche complète (titre / sous-titre). */
watch(
  selectedClient,
  (c) => {
    draftVariant.color_primary = c?.color_primary || ''
    draftVariant.color_secondary = c?.color_secondary || ''
  },
  { immediate: true },
)

watch(selectedClientId, (id) => {
  loadSelectedClientDetail(id)
  schedulePreview()
})

watch(
  () => [signatureText.title, signatureText.subtitle] as const,
  () => schedulePreview(),
)

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
    clients.value = await apiFetch<ClientListItem[]>('/clients')
    if (selectedClientId.value) await loadSelectedClientDetail(selectedClientId.value)
    templates.value = await apiFetch<Template[]>('/templates')
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
    show_side_photo: draftVariant.show_side_photo,
    show_right_logo: draftVariant.show_right_logo,
    show_notes: draftVariant.show_notes,
    color_primary: draftVariant.color_primary,
    color_secondary: draftVariant.color_secondary,
    title: signatureText.title,
    subtitle: signatureText.subtitle,
  })
}

function removeVariant(rowId: string) {
  deliverableVariants.value = deliverableVariants.value.filter((r) => r.id !== rowId)
}

function duplicateVariant(row: DeliverableVariantRow) {
  deliverableVariants.value.push({ ...row, id: crypto.randomUUID() })
}

function loadDraftFromRow(row: DeliverableVariantRow) {
  draftVariant.template_key = row.template_key
  draftVariant.swap_colors = row.swap_colors
  draftVariant.logo_slot = row.logo_slot
  draftVariant.photo1_slot = row.photo1_slot
  draftVariant.photo2_slot = row.photo2_slot
  draftVariant.show_side_photo = row.show_side_photo ?? true
  draftVariant.show_right_logo = row.show_right_logo ?? true
  draftVariant.show_notes = row.show_notes ?? false
  draftVariant.color_primary = row.color_primary ?? ''
  draftVariant.color_secondary = row.color_secondary ?? ''
  signatureText.title = row.title ?? ''
  signatureText.subtitle = row.subtitle ?? ''
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
      show_side_photo: v.show_side_photo ?? true,
      show_right_logo: v.show_right_logo ?? true,
      show_notes: v.show_notes ?? false,
      color_primary: v.color_primary || null,
      color_secondary: v.color_secondary || null,
      ...(v.title?.trim() ? { title: v.title.trim() } : {}),
      ...(v.subtitle?.trim() ? { subtitle: v.subtitle.trim() } : {}),
    }))
    const res = await fetch(`${base}/clients/${selectedClientId.value}/deliverable`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ variants }),
    })
    if (!res.ok) throw new Error(await res.text())

    const blob = await res.blob()
    const bytes = new Uint8Array(await blob.arrayBuffer())

    const root = await ensureDeliverablesRoot()
    const ts = new Date().toISOString().replaceAll(':', '-')
    const safeName = selectedClient.value.name.replaceAll(' ', '_')
    const filename = `signdex_${safeName}_${ts}.zip`
    const filePath = await join(root, filename)
    await writeFile(filePath, bytes)

    await appendDeliverableIndex({
      service: 'signatures',
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
  <UDashboardPanel id="templates">
    <template #header>
      <UDashboardNavbar title="Templates">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <div class="flex items-center gap-2">
            <UButton
              icon="i-lucide-download"
              color="primary"
              variant="solid"
              :loading="generating"
              :disabled="!selectedClientId"
              @click="downloadDeliverable"
            >
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
                <UFormField label="Données injectées dans les templates" class="w-full min-w-0">
                  <USelect
                    v-model="selectedClientId"
                    class="w-full"
                    :items="[
                      { label: '— Aucun (placeholder HTML)', value: null },
                      ...clients.map((c) => ({ label: c.name, value: c.id })),
                    ]"
                    :ui="{
                      base: 'w-full',
                      content: 'z-[300] max-h-72 w-(--reka-select-trigger-width)',
                    }"
                  />
                </UFormField>

                <p class="text-muted text-xs leading-relaxed">
                  <template v-if="!selectedClientId">
                    Aperçu sans client : rendu <strong>placeholder</strong> (pas d’overrides couleur / images).
                  </template>
                  <template v-else>
                    Aperçu et ZIP utilisent la fiche client ; le livrable et l’aperçu sont sous les colonnes Client et Édition.
                  </template>
                </p>

                <p class="text-muted text-xs">
                  Le fichier ZIP nécessite un <strong>client réel</strong>.
                </p>
              </div>
            </UCard>

            <UCard :ui="editorGridColCardUi">
              <template #header>
                <div class="font-semibold">Édition</div>
              </template>

              <template v-if="selectedClientId">
                <div class="grid min-w-0 gap-3 sm:grid-cols-2">
                  <UFormField label="Titre" hint="Remplace le nom en tête (v1/v2). Vide = nom de l'entreprise. Enregistrer pour le ZIP." class="min-w-0 sm:col-span-2">
                    <UInput v-model="signatureText.title" class="w-full" :disabled="!selectedClientId" />
                  </UFormField>
                  <UFormField label="Sous-titre" hint="Ex. fonction, slogan." class="min-w-0 sm:col-span-2">
                    <UInput v-model="signatureText.subtitle" class="w-full" :disabled="!selectedClientId" />
                  </UFormField>
                </div>
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
                <UCheckbox
                  v-if="draftIsSignatureV2"
                  v-model="draftVariant.show_side_photo"
                  label="Afficher la vignette à droite (photo 1)"
                />
                <UCheckbox
                  v-if="draftUsesDualVisualLayout"
                  v-model="draftVariant.show_side_photo"
                  label="Afficher le portrait (photo 1, à gauche)"
                />
                <UCheckbox
                  v-if="draftUsesDualVisualLayout"
                  v-model="draftVariant.show_right_logo"
                  label="Afficher le logo à droite (2e visuel + filet)"
                />
                <UCheckbox
                  v-if="draftShowsNotesOption"
                  v-model="draftVariant.show_notes"
                  label="Afficher l'adresse (1re ligne des notes)"
                />
              </div>
              <div class="grid gap-3 sm:grid-cols-3">
                <UFormField label="Logo affiché" description="Image utilisée à la place du logo du template.">
                  <USelect
                    v-model="draftVariant.logo_slot"
                    class="w-full"
                    :items="IMAGE_SLOT_SELECT_ITEMS"
                    :ui="{ base: 'w-full', content: 'z-[300]' }"
                  />
                </UFormField>
                <UFormField label="Photo 1 affichée" description="Emplacement « photo 1 » dans la signature.">
                  <USelect
                    v-model="draftVariant.photo1_slot"
                    class="w-full"
                    :items="IMAGE_SLOT_SELECT_ITEMS"
                    :ui="{ base: 'w-full', content: 'z-[300]' }"
                  />
                </UFormField>
                <UFormField label="Photo 2 affichée" description="Emplacement « photo 2 » dans la signature.">
                  <USelect
                    v-model="draftVariant.photo2_slot"
                    class="w-full"
                    :items="IMAGE_SLOT_SELECT_ITEMS"
                    :ui="{ base: 'w-full', content: 'z-[300]' }"
                  />
                </UFormField>
              </div>
              <div class="flex flex-wrap gap-2">
                <UButton color="primary" icon="i-lucide-plus" @click="pushDraftToDeliverable">Ajouter au livrable</UButton>
              </div>
            </UCard>
          </div>

          <UCard :ui="editorLivrableCardUi">
            <template #header>
              <div class="flex min-w-0 flex-wrap items-center justify-between gap-2">
                <div class="font-semibold">Livrable — aperçu</div>
                <UButton size="xs" color="neutral" variant="soft" icon="i-lucide-rotate-ccw" @click="resetDeliverableList">
                  Tout réinitialiser
                </UButton>
              </div>
            </template>

            <div v-if="deliverableVariants.length" class="space-y-2">
              <div class="text-muted text-xs font-medium uppercase tracking-wide">
                Dans le livrable ({{ deliverableVariants.length }})
              </div>
              <ul class="flex flex-col gap-2">
                <li
                  v-for="row in deliverableVariants"
                  :key="row.id"
                  class="ring-default flex flex-wrap items-center gap-2 rounded-lg px-3 py-2 ring-1"
                >
                  <div class="min-w-0 flex-1">
                    <div class="truncate text-sm font-medium">{{ templateTitle(row.template_key) }}</div>
                    <div
                      v-if="row.title?.trim() || row.subtitle?.trim()"
                      class="text-muted truncate text-xs"
                    >
                      <span v-if="row.title?.trim()">{{ row.title.trim() }}</span>
                      <span v-if="row.title?.trim() && row.subtitle?.trim()"> · </span>
                      <span v-if="row.subtitle?.trim()">{{ row.subtitle.trim() }}</span>
                    </div>
                  </div>
                  <div class="flex shrink-0 gap-1">
                    <UButton
                      size="xs"
                      color="neutral"
                      variant="ghost"
                      icon="i-lucide-pencil"
                      title="Charger dans l’éditeur"
                      @click="loadDraftFromRow(row)"
                    />
                    <UButton
                      size="xs"
                      color="neutral"
                      variant="ghost"
                      icon="i-lucide-copy"
                      title="Dupliquer"
                      @click="duplicateVariant(row)"
                    />
                    <UButton
                      size="xs"
                      color="neutral"
                      variant="ghost"
                      icon="i-lucide-trash-2"
                      title="Retirer"
                      @click="removeVariant(row.id)"
                    />
                  </div>
                </li>
              </ul>
            </div>
            <p v-else class="text-muted text-sm">Aucune variante dans le livrable pour l’instant.</p>

            <p v-if="!selectedClientId" class="text-muted mt-4 text-sm">
              Aperçu placeholder (sans client) selon le template choisi — sélectionne un client pour données / images réelles.
            </p>
            <p v-else-if="previewLoading" class="text-primary mt-4 text-sm">Mise à jour…</p>

            <div class="ring-default relative mt-4 overflow-hidden rounded-lg ring-1">
              <iframe
                v-if="selectedClientId && previewIframeSrc"
                :src="previewIframeSrc"
                class="h-[min(70vh,640px)] min-h-[420px] w-full bg-white"
                referrerpolicy="no-referrer"
              />
              <div
                v-else-if="selectedClientId && previewLoading"
                class="text-muted flex h-[min(70vh,640px)] min-h-[420px] items-center justify-center bg-white text-sm"
              >
                Préparation de l’aperçu…
              </div>
              <iframe
                v-else-if="placeholderPreviewUrl"
                :key="placeholderPreviewUrl"
                :src="placeholderPreviewUrl"
                class="h-[min(70vh,640px)] min-h-[420px] w-full bg-white"
                referrerpolicy="no-referrer"
              />
              <div v-else class="text-muted p-4 text-sm">Aucun template disponible.</div>
            </div>
          </UCard>
        </div>
      </div>
    </template>
  </UDashboardPanel>

  <SignDexDeliverablePathModal v-model:open="deliverablePathModalOpen" :path="savedZipPath" />
</template>
