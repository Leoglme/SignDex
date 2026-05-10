<script setup lang="ts">
import { join } from '@tauri-apps/api/path'
import { writeFile } from '@tauri-apps/plugin-fs'
import { appendDeliverableIndex, ensureDeliverablesRoot } from '~/composables/useDeliverables'
import { editorClientFormGridCardUi, editorGridColCardUi, editorLivrableCardUi } from '~/constants/editorCardUi'
import { IMAGE_SLOT_SELECT_ITEMS, type ImageSlotSource } from '~/constants/imageSlots'

type Client = {
  id: number
  name: string
  subtitle?: string | null
  firstname?: string | null
  lastname?: string | null
  website_url?: string | null
  email?: string | null
  phone_primary?: string | null
  phone_secondary?: string | null
  linkedin_url?: string | null
  instagram_url?: string | null
  facebook_url?: string | null
  tiktok_url?: string | null
  youtube_url?: string | null
  color_primary?: string | null
  color_secondary?: string | null
  logo_url?: string | null
  photo1_url?: string | null
  photo2_url?: string | null
  notes?: string | null
}

type ImageField = 'logo_url' | 'photo1_url' | 'photo2_url'

type DeliverableVariantRow = {
  id: string
  template_key: string
  swap_colors: boolean
  logo_slot: ImageSlotSource
  photo1_slot: ImageSlotSource
  photo2_slot: ImageSlotSource
  /** Template moderne (signature-v2) : vignette à droite. */
  show_side_photo: boolean
  color_primary: string
  color_secondary: string
}

function emptyToNull(s: string): string | null {
  const t = s.trim()
  return t ? t : null
}

function syncEditFromClient(c: Client) {
  editForm.name = c.name
  editForm.subtitle = c.subtitle ?? ''
  editForm.firstname = c.firstname ?? ''
  editForm.lastname = c.lastname ?? ''
  editForm.website_url = c.website_url ?? ''
  editForm.email = c.email ?? ''
  editForm.phone_primary = c.phone_primary ?? ''
  editForm.phone_secondary = c.phone_secondary ?? ''
  editForm.linkedin_url = c.linkedin_url ?? ''
  editForm.instagram_url = c.instagram_url ?? ''
  editForm.facebook_url = c.facebook_url ?? ''
  editForm.tiktok_url = c.tiktok_url ?? ''
  editForm.youtube_url = c.youtube_url ?? ''
  editForm.color_primary = c.color_primary ?? ''
  editForm.color_secondary = c.color_secondary ?? ''
  editForm.logo_url = c.logo_url ?? ''
  editForm.photo1_url = c.photo1_url ?? ''
  editForm.photo2_url = c.photo2_url ?? ''
  editForm.notes = c.notes ?? ''
}

const route = useRoute()
const id = computed(() => Number(route.params.id))
const client = ref<Client | null>(null)
const templates = ref<{ key: string; title: string; filename: string }[]>([])
const deliverableVariants = ref<DeliverableVariantRow[]>([])
/** Configuration affichée au-dessus de l’aperçu ; « Ajouter au livrable » en fait une ligne du ZIP. */
const draftVariant = reactive({
  template_key: '',
  swap_colors: false,
  logo_slot: 'default' as ImageSlotSource,
  photo1_slot: 'default' as ImageSlotSource,
  photo2_slot: 'default' as ImageSlotSource,
  show_side_photo: true,
  color_primary: '',
  color_secondary: '',
})
const previewIframeSrc = ref<string | null>(null)
const previewLoading = ref(false)
let previewSeq = 0
let previewDebounce: ReturnType<typeof setTimeout> | null = null
const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)
const generating = ref(false)
const uploadingField = ref<ImageField | null>(null)
const deliverablePathModalOpen = ref(false)
const savedZipPath = ref('')
const logoFileRef = ref<HTMLInputElement | null>(null)
const photo1FileRef = ref<HTMLInputElement | null>(null)
const photo2FileRef = ref<HTMLInputElement | null>(null)

const editForm = reactive({
  name: '',
  subtitle: '',
  firstname: '',
  lastname: '',
  website_url: '',
  email: '',
  phone_primary: '',
  phone_secondary: '',
  linkedin_url: '',
  instagram_url: '',
  facebook_url: '',
  tiktok_url: '',
  youtube_url: '',
  color_primary: '',
  color_secondary: '',
  logo_url: '',
  photo1_url: '',
  photo2_url: '',
  notes: '',
})

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

function schedulePreview() {
  if (previewDebounce) clearTimeout(previewDebounce)
  previewDebounce = setTimeout(() => {
    previewDebounce = null
    loadPreview()
  }, 200)
}

async function loadPreview() {
  const c = client.value
  const templateKey = draftVariant.template_key
  if (!c || !templateKey) {
    const prev = previewIframeSrc.value
    previewIframeSrc.value = null
    if (prev) URL.revokeObjectURL(prev)
    return
  }
  const seq = ++previewSeq
  previewLoading.value = true
  try {
    const base = useApiBase()
    const body = {
      template_key: templateKey,
      client_id: c.id,
      swap_colors: draftVariant.swap_colors,
      logo_slot: draftVariant.logo_slot,
      photo1_slot: draftVariant.photo1_slot,
      photo2_slot: draftVariant.photo2_slot,
      show_side_photo: draftVariant.show_side_photo,
      color_primary: draftVariant.color_primary || null,
      color_secondary: draftVariant.color_secondary || null,
    }
    const res = await fetch(`${base}/render/preview`, {
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

watch(
  () => client.value?.id,
  () => schedulePreview(),
)

/**
 * Quand on change de client OU que la fiche client (Modifier le client → Enregistrer) change ses couleurs,
 * on resynchronise les overrides du draft sur les couleurs courantes du client.
 */
watch(
  () => [client.value?.id, client.value?.color_primary, client.value?.color_secondary] as const,
  () => {
    draftVariant.color_primary = client.value?.color_primary || ''
    draftVariant.color_secondary = client.value?.color_secondary || ''
  },
  { immediate: true },
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
    client.value = await apiFetch<Client>(`/clients/${id.value}`)
    templates.value = await apiFetch(`/templates`)
    syncVariantsWithTemplates()
    if (client.value) syncEditFromClient(client.value)
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
    color_primary: draftVariant.color_primary,
    color_secondary: draftVariant.color_secondary,
  })
}

function removeVariant(rowId: string) {
  deliverableVariants.value = deliverableVariants.value.filter((r) => r.id !== rowId)
}

function duplicateVariant(row: DeliverableVariantRow) {
  deliverableVariants.value.push({ ...row, id: crypto.randomUUID() })
}

/** Retire la ligne du livrable et remplit l’éditeur pour ajuster puis ré-ajouter. */
function loadDraftFromRow(row: DeliverableVariantRow) {
  draftVariant.template_key = row.template_key
  draftVariant.swap_colors = row.swap_colors
  draftVariant.logo_slot = row.logo_slot
  draftVariant.photo1_slot = row.photo1_slot
  draftVariant.photo2_slot = row.photo2_slot
  draftVariant.show_side_photo = row.show_side_photo ?? true
  draftVariant.color_primary = row.color_primary ?? ''
  draftVariant.color_secondary = row.color_secondary ?? ''
  removeVariant(row.id)
}

function resetDeliverableList() {
  deliverableVariants.value = []
}

function buildUpdatePayload() {
  return {
    name: editForm.name.trim(),
    subtitle: emptyToNull(editForm.subtitle),
    firstname: emptyToNull(editForm.firstname),
    lastname: emptyToNull(editForm.lastname),
    website_url: emptyToNull(editForm.website_url),
    email: emptyToNull(editForm.email),
    phone_primary: emptyToNull(editForm.phone_primary),
    phone_secondary: emptyToNull(editForm.phone_secondary),
    linkedin_url: emptyToNull(editForm.linkedin_url),
    instagram_url: emptyToNull(editForm.instagram_url),
    facebook_url: emptyToNull(editForm.facebook_url),
    tiktok_url: emptyToNull(editForm.tiktok_url),
    youtube_url: emptyToNull(editForm.youtube_url),
    color_primary: emptyToNull(editForm.color_primary),
    color_secondary: emptyToNull(editForm.color_secondary),
    logo_url: emptyToNull(editForm.logo_url),
    photo1_url: emptyToNull(editForm.photo1_url),
    photo2_url: emptyToNull(editForm.photo2_url),
    notes: emptyToNull(editForm.notes),
  }
}

async function saveClient() {
  if (!editForm.name.trim()) return
  saving.value = true
  error.value = null
  try {
    const updated = await apiFetch<Client>(`/clients/${id.value}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildUpdatePayload()),
    })
    client.value = updated
    syncEditFromClient(updated)
    schedulePreview()
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    saving.value = false
  }
}

async function onUploadAsset(field: ImageField, ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || !client.value) return
  uploadingField.value = field
  error.value = null
  try {
    const base = useApiBase()
    const fd = new FormData()
    fd.append('file', file)
    const res = await fetch(`${base}/clients/${client.value.id}/upload?field=${field}`, {
      method: 'POST',
      body: fd,
    })
    if (!res.ok) throw new Error(await res.text())
    const data = (await res.json()) as { url: string }
    client.value = { ...client.value, [field]: data.url }
    editForm[field] = data.url
    schedulePreview()
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    uploadingField.value = null
  }
}

async function downloadDeliverable() {
  if (!client.value) return
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
      color_primary: v.color_primary || null,
      color_secondary: v.color_secondary || null,
    }))
    const res = await fetch(`${base}/clients/${client.value.id}/deliverable`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ variants }),
    })
    if (!res.ok) throw new Error(await res.text())

    const blob = await res.blob()
    const arrayBuf = await blob.arrayBuffer()
    const bytes = new Uint8Array(arrayBuf)

    const root = await ensureDeliverablesRoot()
    const ts = new Date().toISOString().replaceAll(':', '-')
    const filename = `signdex_${client.value.name.replaceAll(' ', '_')}_${ts}.zip`
    const filePath = await join(root, filename)
    await writeFile(filePath, bytes)

    await appendDeliverableIndex({
      service: 'signatures',
      clientId: client.value.id,
      clientName: client.value.name,
      createdAtIso: new Date().toISOString(),
      zipPath: filePath,
      variants,
    })

    savedZipPath.value = filePath
    deliverablePathModalOpen.value = true
  } catch (e: any) {
    const msg = e?.message || String(e)
    error.value = msg
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <UDashboardPanel :id="`client-${id}`">
    <template #header>
      <UDashboardNavbar :title="client?.name || 'Client'">
        <template #leading>
          <div class="flex items-center gap-1">
            <UDashboardSidebarCollapse />
            <UButton to="/" color="neutral" variant="ghost" icon="i-lucide-arrow-left" />
          </div>
        </template>
        <template #right>
          <div class="flex items-center gap-2">
            <UButton to="/deliverables" color="neutral" variant="ghost" icon="i-lucide-package" />
            <UButton color="primary" variant="solid" :loading="generating" @click="downloadDeliverable">
              Télécharger le livrable
            </UButton>
          </div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="space-y-4">
        <UAlert v-if="error" color="red" variant="soft" title="Erreur" :description="error" />

        <div v-if="loading" class="text-muted text-sm">Chargement…</div>

        <div v-else-if="client" class="min-w-0 space-y-4">
          <div
            class="grid min-w-0 items-stretch gap-4 lg:grid-cols-[minmax(16rem,26rem)_minmax(0,1fr)] xl:grid-cols-[minmax(18rem,28rem)_minmax(0,1fr)]"
          >
            <UCard :ui="editorClientFormGridCardUi">
              <template #header>
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <div class="font-semibold">Modifier le client</div>
                  <UButton color="primary" size="sm" :loading="saving" :disabled="!editForm.name.trim()" @click="saveClient">
                    Enregistrer
                  </UButton>
                </div>
              </template>

              <div class="min-h-0 flex-1 space-y-6 overflow-y-auto">
              <div class="grid min-w-0 gap-3 sm:grid-cols-2">
                <UFormField label="Nom de l'entreprise" hint="Sert d'identifiant et de marque." class="min-w-0 sm:col-span-2">
                  <UInput v-model="editForm.name" class="w-full" />
                </UFormField>
                <UFormField label="Prénom (contact)" class="min-w-0">
                  <UInput v-model="editForm.firstname" class="w-full" />
                </UFormField>
                <UFormField label="Nom (contact)" class="min-w-0">
                  <UInput v-model="editForm.lastname" class="w-full" />
                </UFormField>
                <UFormField label="Sous-titre / slogan" class="min-w-0 sm:col-span-2">
                  <UInput v-model="editForm.subtitle" class="w-full" />
                </UFormField>
                <UFormField label="Site web" class="min-w-0 sm:col-span-2">
                  <UInput v-model="editForm.website_url" class="w-full" placeholder="https://…" />
                </UFormField>
                <UFormField label="Email" class="min-w-0 sm:col-span-2">
                  <UInput v-model="editForm.email" class="w-full" />
                </UFormField>
                <UFormField label="Téléphone 1" class="min-w-0">
                  <UInput v-model="editForm.phone_primary" class="w-full" />
                </UFormField>
                <UFormField label="Téléphone 2" class="min-w-0">
                  <UInput v-model="editForm.phone_secondary" class="w-full" />
                </UFormField>
                <UFormField label="LinkedIn" class="min-w-0 sm:col-span-2">
                  <UInput v-model="editForm.linkedin_url" class="w-full" />
                </UFormField>
                <UFormField label="Instagram" class="min-w-0">
                  <UInput v-model="editForm.instagram_url" class="w-full" />
                </UFormField>
                <UFormField label="Facebook" class="min-w-0">
                  <UInput v-model="editForm.facebook_url" class="w-full" />
                </UFormField>
                <UFormField label="TikTok" class="min-w-0">
                  <UInput v-model="editForm.tiktok_url" class="w-full" />
                </UFormField>
                <UFormField label="YouTube" class="min-w-0">
                  <UInput v-model="editForm.youtube_url" class="w-full" />
                </UFormField>
                <UFormField label="Couleur 1" class="min-w-0">
                  <UInput v-model="editForm.color_primary" class="w-full" placeholder="#4e8baa" />
                </UFormField>
                <UFormField label="Couleur 2" class="min-w-0">
                  <UInput v-model="editForm.color_secondary" class="w-full" placeholder="#5a9abf" />
                </UFormField>
                <UFormField label="Notes" class="min-w-0 sm:col-span-2">
                  <textarea
                    v-model="editForm.notes"
                    rows="3"
                    class="focus:ring-primary block w-full resize-y rounded-md border-0 bg-elevated px-3 py-2 text-sm ring ring-default focus:outline-none focus:ring-2"
                  />
                </UFormField>
              </div>

              <div class="border-default space-y-4 border-t pt-4">
                <div class="text-muted text-xs font-medium uppercase tracking-wide">Images</div>
                <p class="text-muted text-xs">
                  URL ou envoi fichier (nécessite Supabase configuré côté API).
                </p>

                <div class="space-y-3">
                  <div class="rounded-lg bg-elevated/60 p-3 ring ring-default">
                    <div class="mb-2 text-sm font-medium">Logo</div>
                    <div class="flex gap-3">
                      <img
                        v-if="editForm.logo_url"
                        :src="editForm.logo_url"
                        alt=""
                        class="size-14 shrink-0 rounded bg-white object-contain ring ring-default"
                      />
                      <div class="min-w-0 flex-1 space-y-2">
                        <UInput v-model="editForm.logo_url" class="w-full" placeholder="URL du logo" />
                        <div>
                          <input
                            ref="logoFileRef"
                            type="file"
                            accept="image/*"
                            class="hidden"
                            @change="onUploadAsset('logo_url', $event)"
                          />
                          <UButton
                            type="button"
                            color="neutral"
                            variant="soft"
                            size="xs"
                            :loading="uploadingField === 'logo_url'"
                            icon="i-lucide-upload"
                            @click="logoFileRef?.click()"
                          >
                            Envoyer un fichier
                          </UButton>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="rounded-lg bg-elevated/60 p-3 ring ring-default">
                    <div class="mb-2 text-sm font-medium">Photo 1</div>
                    <div class="flex gap-3">
                      <img
                        v-if="editForm.photo1_url"
                        :src="editForm.photo1_url"
                        alt=""
                        class="size-14 shrink-0 rounded-full bg-white object-cover ring ring-default"
                      />
                      <div class="min-w-0 flex-1 space-y-2">
                        <UInput v-model="editForm.photo1_url" class="w-full" placeholder="URL photo 1" />
                        <div>
                          <input
                            ref="photo1FileRef"
                            type="file"
                            accept="image/*"
                            class="hidden"
                            @change="onUploadAsset('photo1_url', $event)"
                          />
                          <UButton
                            type="button"
                            color="neutral"
                            variant="soft"
                            size="xs"
                            :loading="uploadingField === 'photo1_url'"
                            icon="i-lucide-upload"
                            @click="photo1FileRef?.click()"
                          >
                            Envoyer un fichier
                          </UButton>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="rounded-lg bg-elevated/60 p-3 ring ring-default">
                    <div class="mb-2 text-sm font-medium">Photo 2</div>
                    <div class="flex gap-3">
                      <img
                        v-if="editForm.photo2_url"
                        :src="editForm.photo2_url"
                        alt=""
                        class="size-14 shrink-0 rounded bg-white object-cover ring ring-default"
                      />
                      <div class="min-w-0 flex-1 space-y-2">
                        <UInput v-model="editForm.photo2_url" class="w-full" placeholder="URL photo 2" />
                        <div>
                          <input
                            ref="photo2FileRef"
                            type="file"
                            accept="image/*"
                            class="hidden"
                            @change="onUploadAsset('photo2_url', $event)"
                          />
                          <UButton
                            type="button"
                            color="neutral"
                            variant="soft"
                            size="xs"
                            :loading="uploadingField === 'photo2_url'"
                            icon="i-lucide-upload"
                            @click="photo2FileRef?.click()"
                          >
                            Envoyer un fichier
                          </UButton>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
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
                :default-color1="client?.color_primary || null"
                :default-color2="client?.color_secondary || null"
              />
              <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
                <UCheckbox v-model="draftVariant.swap_colors" label="Échanger couleurs 1 ↔ 2" />
                <UCheckbox
                  v-if="draftIsSignatureV2"
                  v-model="draftVariant.show_side_photo"
                  label="Afficher la vignette à droite (photo 1)"
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
              <div class="flex min-w-0 flex-col gap-3">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <div class="font-semibold">Livrable — aperçu</div>
                  <UButton size="xs" color="neutral" variant="soft" icon="i-lucide-rotate-ccw" @click="resetDeliverableList">
                    Tout réinitialiser
                  </UButton>
                </div>
                <p class="text-muted text-xs leading-relaxed">
                  Liste des variantes dans le ZIP et aperçu HTML selon la configuration dans Édition (doublons → noms _variant-2, …).
                </p>
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
                  <span class="min-w-0 flex-1 truncate text-sm font-medium">{{ templateTitle(row.template_key) }}</span>
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

            <div class="text-muted mt-4 text-sm">
              Aperçu HTML — même configuration que dans Édition.
              <span v-if="previewLoading" class="text-primary ml-2">Mise à jour…</span>
            </div>

            <div class="ring-default relative mt-4 overflow-hidden rounded-lg ring-1">
              <iframe
                v-if="previewIframeSrc"
                :src="previewIframeSrc"
                class="h-[min(70vh,640px)] min-h-[420px] w-full bg-white"
                referrerpolicy="no-referrer"
              />
              <div v-else class="text-muted p-4 text-sm">Sélectionne un template pour l’aperçu.</div>
            </div>
          </UCard>
        </div>
      </div>
    </template>
  </UDashboardPanel>

  <SignDexDeliverablePathModal v-model:open="deliverablePathModalOpen" :path="savedZipPath" />
</template>
