<template>
  <UDashboardPanel id="mon-espace" :ui="{ body: 'p-3 sm:p-6 bg-neutral-100 dark:bg-transparent' }">
    <template #header>
      <UDashboardNavbar title="Mes signatures">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <UButton icon="i-lucide-refresh-cw" color="neutral" variant="ghost" :loading="loading" @click="load" />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="w-full pb-6">
        <UAlert v-if="error" color="error" variant="soft" icon="i-lucide-triangle-alert" title="Erreur" :description="error" class="mb-6" />

        <!-- Première ligne : orga + actions -->
        <div class="flex flex-wrap items-end justify-between gap-4">
          <div class="min-w-0">
            <h1 class="text-highlighted text-2xl font-semibold">{{ overview?.organization.name || 'Mon espace' }}</h1>
            <p class="text-muted mt-1 text-sm">
              {{ overview?.organization.member_count ?? 0 }} collaborateurs · {{ overview?.organization.signature_count ?? 0 }} signatures prêtes
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <UButton icon="i-lucide-user-plus" size="lg" color="neutral" :style="brandButtonStyle" label="Ajouter un collaborateur" @click="openAdd" />
            <UButton icon="i-lucide-download" size="lg" color="neutral" variant="soft" :loading="downloadingAll" :disabled="!overview?.members.length" label="Tout télécharger" @click="downloadAll" />
          </div>
        </div>

        <!-- Recherche + filtre bureau -->
        <div class="mt-8 flex flex-wrap items-center gap-3">
          <UInput v-model="search" icon="i-lucide-search" placeholder="Rechercher une personne…" class="min-w-56 flex-1" size="lg" />
          <USelect v-model="officeFilter" :items="officeOptions" icon="i-lucide-map-pin" size="lg" class="w-full sm:w-56" />
        </div>

        <!-- Liste -->
        <div class="mt-6">
          <div v-if="loading" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <USkeleton v-for="i in 6" :key="i" class="h-28 w-full rounded-2xl bg-neutral-200 dark:bg-neutral-800" />
          </div>
          <div v-else-if="filteredMembers.length" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <div
              v-for="m in filteredMembers"
              :key="m.id"
              class="bg-default ring-default rounded-2xl p-5 shadow-sm ring-1 dark:bg-elevated/60 dark:shadow-none"
            >
              <div class="flex items-center gap-3">
                <span
                  class="flex size-11 shrink-0 items-center justify-center rounded-full text-sm font-semibold text-white"
                  :style="{ background: avatarColor(m) }"
                >
                  {{ initials(m) }}
                </span>
                <div class="min-w-0 flex-1">
                  <p class="text-highlighted truncate font-medium">{{ memberName(m) }}</p>
                  <p v-if="m.title" class="text-muted truncate text-sm">{{ m.title }}</p>
                </div>
                <UButton icon="i-lucide-eye" color="neutral" variant="ghost" size="sm" title="Aperçu" :disabled="!m.offices.length" :aria-label="`Aperçu de ${memberName(m)}`" @click="openPreview(m)" />
                <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" size="sm" title="Modifier" :aria-label="`Modifier ${memberName(m)}`" @click="openEdit(m)" />
                <UButton icon="i-lucide-download" color="neutral" variant="ghost" size="sm" title="Télécharger" :loading="downloadingMember === m.id" :disabled="!m.offices.length" :aria-label="`Télécharger la signature de ${memberName(m)}`" @click="downloadMember(m)" />
              </div>
              <div class="text-muted mt-3 flex items-center gap-1.5 text-sm">
                <UIcon name="i-lucide-map-pin" class="size-3.5 shrink-0 opacity-70" />
                <span class="truncate">{{ m.offices.map(o => o.label).join(' · ') || 'Aucun bureau' }}</span>
              </div>
            </div>
          </div>
          <div v-else class="text-muted border-default rounded-2xl border border-dashed p-10 text-center text-sm">
            Aucun collaborateur ne correspond à votre recherche.
          </div>
        </div>
      </div>
    </template>
  </UDashboardPanel>

  <!-- Panneau ajout / modification -->
  <USlideover v-model:open="formOpen" :title="editingId ? 'Modifier le collaborateur' : 'Ajouter un collaborateur'">
    <template #body>
      <div class="space-y-5">
        <div class="grid grid-cols-2 gap-3">
          <UFormField label="Prénom">
            <UInput v-model="form.firstname" placeholder="Alex" class="w-full" />
          </UFormField>
          <UFormField label="Nom">
            <UInput v-model="form.lastname" placeholder="Martin" class="w-full" />
          </UFormField>
        </div>
        <UFormField label="Fonction">
          <div class="relative" @focusin="titleFocused = true" @focusout="onTitleFocusOut">
            <UInput
              v-model="form.title"
              placeholder="Stagiaire, Avocat, Paralegal…"
              class="w-full"
              autocomplete="off"
            />
            <div
              v-if="showTitleMenu"
              class="ring-default bg-default absolute z-[60] mt-1 max-h-56 w-full overflow-auto rounded-lg shadow-lg ring-1"
            >
              <button
                v-for="s in titleMatches"
                :key="s"
                type="button"
                class="text-highlighted hover:bg-elevated block w-full cursor-pointer truncate px-3 py-2 text-left text-sm"
                @mousedown.prevent="pickTitle(s)"
              >
                {{ s }}
              </button>
            </div>
          </div>
        </UFormField>
        <div>
          <p class="text-highlighted mb-1 text-sm font-medium">Bureaux</p>
          <p class="text-muted mb-2 text-xs">Cochez les bureaux de cette personne. Une signature sera générée par bureau.</p>
          <div class="space-y-1">
            <label
              v-for="o in offices"
              :key="o.id"
              class="hover:bg-elevated/50 flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-2"
            >
              <UCheckbox :model-value="form.office_ids.includes(o.id)" @update:model-value="(v: boolean) => setOffice(o.id, v)" />
              <span class="text-sm">{{ o.label }}</span>
              <span v-if="o.address_cp_city" class="text-muted text-xs">— {{ o.address_cp_city }}</span>
            </label>
          </div>
        </div>
      </div>
    </template>
    <template #footer>
      <div class="flex w-full items-center gap-2">
        <UButton v-if="editingId" color="error" variant="ghost" icon="i-lucide-trash-2" label="Supprimer" @click="confirmDeleteOpen = true" />
        <div class="ml-auto flex gap-2">
          <UButton color="neutral" variant="ghost" label="Annuler" @click="formOpen = false" />
          <UButton icon="i-lucide-save" color="neutral" :style="brandButtonStyle" :loading="saving" :disabled="!canSave" label="Enregistrer" @click="save" />
        </div>
      </div>
    </template>
  </USlideover>

  <!-- Aperçu des signatures du collaborateur -->
  <UModal v-model:open="previewOpen" :title="`Aperçu — ${previewName}`" :ui="{ content: 'sm:max-w-3xl' }">
    <template #body>
      <div v-if="previewLoading" class="space-y-3">
        <USkeleton class="h-72 w-full rounded-lg bg-neutral-200 dark:bg-neutral-800" />
      </div>
      <div v-else-if="previewSigs.length" class="space-y-5">
        <div v-for="sig in previewSigs" :key="sig.office_label">
          <p class="text-highlighted mb-1.5 flex items-center gap-1.5 text-sm font-medium">
            <UIcon name="i-lucide-map-pin" class="size-3.5 opacity-70" />{{ sig.office_label }}
          </p>
          <iframe :srcdoc="sig.html" title="Aperçu de la signature" class="ring-default w-full rounded-lg bg-white ring-1" style="height: 380px" />
        </div>
      </div>
      <p v-else class="text-muted text-sm">Ce collaborateur n'a aucun bureau — aucune signature à afficher.</p>
    </template>
    <template #footer>
      <div class="ml-auto flex gap-2">
        <UButton color="neutral" variant="ghost" label="Fermer" @click="previewOpen = false" />
        <UButton
          v-if="previewMember && previewMember.offices.length"
          icon="i-lucide-download"
          color="neutral"
          :style="brandButtonStyle"
          :loading="downloadingMember === previewMember.id"
          label="Télécharger"
          @click="downloadMember(previewMember)"
        />
      </div>
    </template>
  </UModal>

  <!-- Confirmation de suppression (vraie modale UI) -->
  <UModal v-model:open="confirmDeleteOpen" title="Supprimer le collaborateur">
    <template #body>
      <p class="text-muted text-sm">
        Supprimer <span class="text-highlighted font-medium">{{ editingName }}</span> ? Sa signature ne sera plus générée. Cette action est irréversible.
      </p>
    </template>
    <template #footer>
      <div class="ml-auto flex gap-2">
        <UButton color="neutral" variant="ghost" label="Annuler" @click="confirmDeleteOpen = false" />
        <UButton color="error" icon="i-lucide-trash-2" :loading="removing" label="Supprimer" @click="doRemove" />
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import type { ComputedRef } from 'vue'
import type { PortalMember, PortalOffice, PortalOverview } from '~/types/portal'

definePageMeta({ layout: 'portal' })
useHead({ title: 'Mes signatures' })

const toast = useToast()
const { brandButtonStyle } = useBrand()

// SSR : les données sont récupérées côté serveur → au reload, la page arrive déjà remplie
// (pas de skeleton). En navigation client / refresh manuel, `refresh()` recharge (skeleton).
const { data: overview, status, error: overviewError, refresh } = await useAsyncData<PortalOverview>(
  'portal-overview',
  () => apiFetch<PortalOverview>('/portal/overview'),
)
const loading: ComputedRef<boolean> = computed(() => status.value === 'pending')
const error: ComputedRef<string | null> = computed(() =>
  overviewError.value ? (overviewError.value.message || 'Chargement impossible') : null,
)
const downloadingAll = ref(false)
const downloadingMember = ref<number | null>(null)

const search = ref('')
const officeFilter = ref('all')

const formOpen = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const removing = ref(false)
const confirmDeleteOpen = ref(false)
const previewOpen = ref(false)
const previewLoading = ref(false)
const previewName = ref('')
const previewMember = ref<PortalMember | null>(null)
const previewSigs = ref<{ office_label: string, html: string }[]>([])
const form = reactive<{ firstname: string, lastname: string, title: string, office_ids: number[] }>({
  firstname: '',
  lastname: '',
  title: '',
  office_ids: [],
})

const AVATAR_PALETTE = ['#0ea5e9', '#22c55e', '#f59e0b', '#a855f7', '#ec4899', '#14b8a6', '#ef4444', '#6366f1']

const offices: ComputedRef<PortalOffice[]> = computed(() => overview.value?.offices || [])

function memberName(m: PortalMember): string {
  return [m.firstname, m.lastname].filter(Boolean).join(' ') || 'Collaborateur'
}

function initials(m: PortalMember): string {
  const parts = [m.firstname, m.lastname].filter(Boolean) as string[]
  const letters = parts.length ? parts.map(p => p[0]).join('') : memberName(m).slice(0, 2)
  return letters.slice(0, 2).toUpperCase()
}

function avatarColor(m: PortalMember): string {
  let sum = 0
  for (const ch of memberName(m)) sum += ch.charCodeAt(0)
  return AVATAR_PALETTE[sum % AVATAR_PALETTE.length]!
}

const officeOptions: ComputedRef<{ label: string, value: string }[]> = computed(() => {
  const set = new Set<string>()
  for (const m of overview.value?.members || []) {
    for (const o of m.offices) set.add(o.label)
  }
  return [{ label: 'Tous les bureaux', value: 'all' }, ...[...set].sort().map(l => ({ label: l, value: l }))]
})

const filteredMembers: ComputedRef<PortalMember[]> = computed(() => {
  let list = overview.value?.members || []
  const q = search.value.trim().toLowerCase()
  if (q) list = list.filter(m => memberName(m).toLowerCase().includes(q) || (m.title || '').toLowerCase().includes(q))
  if (officeFilter.value && officeFilter.value !== 'all') {
    list = list.filter(m => m.offices.some(o => o.label === officeFilter.value))
  }
  return list
})

const canSave: ComputedRef<boolean> = computed(() => Boolean(form.firstname.trim() || form.lastname.trim()))
const editingName: ComputedRef<string> = computed(() => [form.firstname, form.lastname].filter(Boolean).join(' ').trim() || 'ce collaborateur')

// Autocomplete « Fonction » : champ texte LIBRE + suggestions des fonctions déjà utilisées.
// Cliquer une suggestion pré-remplit le champ ; le texte reste ensuite entièrement éditable.
const titleFocused = ref(false)
const titleSuggestions: ComputedRef<string[]> = computed(() => {
  const set = new Set<string>()
  for (const m of overview.value?.members || []) {
    if (m.title && m.title.trim()) set.add(m.title.trim())
  }
  return [...set].sort()
})
const titleMatches: ComputedRef<string[]> = computed(() => {
  const q = form.title.trim().toLowerCase()
  // Exclut la correspondance exacte → le menu se referme tout seul après une sélection.
  return titleSuggestions.value.filter(s => s.toLowerCase().includes(q) && s.toLowerCase() !== q).slice(0, 8)
})
const showTitleMenu: ComputedRef<boolean> = computed(() => titleFocused.value && titleMatches.value.length > 0)
function pickTitle(s: string): void {
  form.title = s
}
function onTitleFocusOut(): void {
  window.setTimeout(() => { titleFocused.value = false }, 150)
}

function setOffice(id: number, checked: boolean): void {
  const has = form.office_ids.includes(id)
  if (checked && !has) form.office_ids.push(id)
  if (!checked && has) form.office_ids = form.office_ids.filter(x => x !== id)
}

function openAdd(): void {
  editingId.value = null
  form.firstname = ''
  form.lastname = ''
  form.title = ''
  form.office_ids = offices.value.map(o => o.id)
  formOpen.value = true
}

function openEdit(m: PortalMember): void {
  editingId.value = m.id
  form.firstname = m.firstname || ''
  form.lastname = m.lastname || ''
  form.title = m.title || ''
  form.office_ids = m.offices.map(o => o.id)
  formOpen.value = true
}

async function openPreview(m: PortalMember): Promise<void> {
  previewMember.value = m
  previewName.value = memberName(m)
  previewSigs.value = []
  previewOpen.value = true
  previewLoading.value = true
  try {
    const res = await apiFetch<{ member_name: string, signatures: { office_label: string, html: string }[] }>(`/portal/members/${m.id}/preview`)
    previewSigs.value = res.signatures
  } catch (e) {
    toast.add({ title: 'Aperçu impossible', description: (e as Error).message, color: 'error' })
    previewOpen.value = false
  } finally {
    previewLoading.value = false
  }
}

async function load(): Promise<void> {
  await refresh()
}

async function save(): Promise<void> {
  if (!canSave.value) return
  saving.value = true
  try {
    const body = {
      firstname: form.firstname.trim() || null,
      lastname: form.lastname.trim() || null,
      title: form.title.trim() || null,
      office_ids: form.office_ids,
    }
    if (editingId.value) {
      await apiFetch(`/portal/members/${editingId.value}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      toast.add({ title: 'Collaborateur mis à jour', color: 'success', icon: 'i-lucide-check' })
    } else {
      await apiFetch('/portal/members', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      toast.add({ title: 'Collaborateur ajouté', description: 'Vous pouvez télécharger sa signature depuis sa carte.', color: 'success', icon: 'i-lucide-check' })
    }
    formOpen.value = false
    await load()
  } catch (e) {
    toast.add({ title: 'Enregistrement impossible', description: (e as Error).message, color: 'error' })
  } finally {
    saving.value = false
  }
}

async function doRemove(): Promise<void> {
  if (!editingId.value) return
  removing.value = true
  try {
    await apiFetch(`/portal/members/${editingId.value}`, { method: 'DELETE' })
    confirmDeleteOpen.value = false
    formOpen.value = false
    await load()
    toast.add({ title: 'Collaborateur supprimé', color: 'success' })
  } catch (e) {
    toast.add({ title: 'Suppression impossible', description: (e as Error).message, color: 'error' })
  } finally {
    removing.value = false
  }
}

async function downloadZip(path: string, filename: string): Promise<void> {
  const base = useApiBase()
  const res = await fetch(`${base}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders() }, body: '{}' })
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText))
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function stamp(): string {
  return new Date().toISOString().slice(0, 10)
}

async function runDownload(path: string, filename: string, toastId: string, waitMsg: string): Promise<void> {
  toast.add({ id: toastId, title: 'Génération en cours…', description: waitMsg, color: 'info', icon: 'i-lucide-loader-circle', duration: 0 })
  try {
    await downloadZip(path, filename)
    toast.remove(toastId)
    toast.add({ title: 'Téléchargement prêt', color: 'success', icon: 'i-lucide-download' })
  } catch (e) {
    toast.remove(toastId)
    toast.add({ title: 'Téléchargement impossible', description: (e as Error).message, color: 'error' })
  }
}

async function downloadAll(): Promise<void> {
  downloadingAll.value = true
  try {
    await runDownload('/portal/deliverable', `signatures_${stamp()}.zip`, 'dl-all', 'Génération de toutes les signatures — cela peut prendre jusqu\'à une minute.')
  } finally {
    downloadingAll.value = false
  }
}

async function downloadMember(m: PortalMember): Promise<void> {
  downloadingMember.value = m.id
  try {
    const slug = memberName(m).replace(/\s+/g, '-').toLowerCase()
    await runDownload(`/portal/members/${m.id}/deliverable`, `signature_${slug}_${stamp()}.zip`, `dl-${m.id}`, 'Génération de la signature en cours…')
  } finally {
    downloadingMember.value = null
  }
}
</script>
