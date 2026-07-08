<script setup lang="ts">
import { join } from '@tauri-apps/api/path'
import { writeFile } from '@tauri-apps/plugin-fs'
import { appendDeliverableIndex, ensureDeliverablesRoot } from '~/composables/useDeliverables'

type Office = { id: number; label: string; template_key: string; sort_order: number }
type Member = {
  id: number
  firstname?: string | null
  lastname?: string | null
  title?: string | null
  sort_order: number
  offices: Office[]
}
type OrgDetail = {
  id: number
  name: string
  slug: string
  notes?: string | null
  show_chambers: boolean
  show_phone: boolean
  offices: Office[]
  members: Member[]
}
type TemplateInfo = { key: string; title: string; filename: string }

const route = useRoute()
const id = computed(() => Number(route.params.id))

const org = ref<OrgDetail | null>(null)
const templates = ref<TemplateInfo[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const generatingAll = ref(false)
const generatingMemberId = ref<number | null>(null)

const deliverablePathModalOpen = ref(false)
const savedZipPath = ref('')

// --- ajout bureau ---
const newOffice = reactive({ label: '', template_key: '' })
const addingOffice = ref(false)

// --- modal membre (création / édition) ---
const memberModalOpen = ref(false)
const savingMember = ref(false)
const memberDraft = reactive({
  id: null as number | null,
  firstname: '',
  lastname: '',
  title: '',
  office_ids: [] as number[],
})

const templateItems = computed(() => templates.value.map((t) => ({ label: t.title, value: t.key })))
const signatureCount = computed(
  () => org.value?.members.reduce((acc, m) => acc + (m.offices?.length || 0), 0) ?? 0,
)

function templateTitle(key: string) {
  return templates.value.find((t) => t.key === key)?.title ?? key
}
function memberName(m: { firstname?: string | null; lastname?: string | null }) {
  return [m.firstname, m.lastname].filter(Boolean).join(' ') || 'Sans nom'
}

async function refresh() {
  loading.value = true
  error.value = null
  try {
    const [o, t] = await Promise.all([
      apiFetch<OrgDetail>(`/organizations/${id.value}`),
      apiFetch<TemplateInfo[]>(`/templates`),
    ])
    org.value = o
    templates.value = t
    if (!newOffice.template_key) {
      newOffice.template_key = t.find((x) => x.key.startsWith('signature-lexial'))?.key || t[0]?.key || ''
    }
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

await refresh()

// ---------- Option : logo Chambers (2e image) ----------
async function setShowChambers(value: boolean) {
  if (!org.value) return
  const prev = org.value.show_chambers
  org.value.show_chambers = value
  error.value = null
  try {
    await apiFetch(`/organizations/${org.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ show_chambers: value }),
    })
  } catch (e: any) {
    org.value.show_chambers = prev
    error.value = e?.message || String(e)
  }
}

// ---------- Option : téléphone dans la signature ----------
async function setShowPhone(value: boolean) {
  if (!org.value) return
  const prev = org.value.show_phone
  org.value.show_phone = value
  error.value = null
  try {
    await apiFetch(`/organizations/${org.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ show_phone: value }),
    })
  } catch (e: any) {
    org.value.show_phone = prev
    error.value = e?.message || String(e)
  }
}

// ---------- Bureaux ----------
async function addOffice() {
  if (!org.value || !newOffice.label.trim() || !newOffice.template_key) return
  addingOffice.value = true
  error.value = null
  try {
    await apiFetch(`/organizations/${org.value.id}/offices`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        label: newOffice.label.trim(),
        template_key: newOffice.template_key,
        sort_order: org.value.offices.length,
      }),
    })
    newOffice.label = ''
    await refresh()
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    addingOffice.value = false
  }
}

async function deleteOffice(officeId: number) {
  if (!org.value) return
  error.value = null
  try {
    await apiFetch(`/organizations/${org.value.id}/offices/${officeId}`, { method: 'DELETE' })
    await refresh()
  } catch (e: any) {
    error.value = e?.message || String(e)
  }
}

// ---------- Membres ----------
function openCreateMember() {
  memberDraft.id = null
  memberDraft.firstname = ''
  memberDraft.lastname = ''
  memberDraft.title = ''
  memberDraft.office_ids = org.value ? org.value.offices.map((o) => o.id) : []
  memberModalOpen.value = true
}

function openEditMember(m: Member) {
  memberDraft.id = m.id
  memberDraft.firstname = m.firstname ?? ''
  memberDraft.lastname = m.lastname ?? ''
  memberDraft.title = m.title ?? ''
  memberDraft.office_ids = m.offices.map((o) => o.id)
  memberModalOpen.value = true
}

function toggleDraftOffice(officeId: number, checked: boolean) {
  const set = new Set(memberDraft.office_ids)
  if (checked) set.add(officeId)
  else set.delete(officeId)
  memberDraft.office_ids = [...set]
}

async function saveMember() {
  if (!org.value) return
  savingMember.value = true
  error.value = null
  try {
    const body = JSON.stringify({
      firstname: memberDraft.firstname.trim() || null,
      lastname: memberDraft.lastname.trim() || null,
      title: memberDraft.title.trim() || null,
      office_ids: memberDraft.office_ids,
    })
    if (memberDraft.id == null) {
      await apiFetch(`/organizations/${org.value.id}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
      })
    } else {
      await apiFetch(`/organizations/${org.value.id}/members/${memberDraft.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body,
      })
    }
    memberModalOpen.value = false
    await refresh()
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    savingMember.value = false
  }
}

async function deleteMember(memberId: number) {
  if (!org.value) return
  error.value = null
  try {
    await apiFetch(`/organizations/${org.value.id}/members/${memberId}`, { method: 'DELETE' })
    await refresh()
  } catch (e: any) {
    error.value = e?.message || String(e)
  }
}

// ---------- Génération livrable (1 clic) ----------
async function saveZipBlob(res: Response, slug: string) {
  if (!res.ok) throw new Error(await res.text())
  const bytes = new Uint8Array(await (await res.blob()).arrayBuffer())
  const root = await ensureDeliverablesRoot()
  const ts = new Date().toISOString().replaceAll(':', '-')
  const filePath = await join(root, `signdex_${slug}_${ts}.zip`)
  await writeFile(filePath, bytes)
  await appendDeliverableIndex({
    kind: 'organization',
    service: 'organization',
    clientId: org.value!.id,
    clientName: org.value!.name,
    createdAtIso: new Date().toISOString(),
    zipPath: filePath,
  })
  savedZipPath.value = filePath
  deliverablePathModalOpen.value = true
}

async function generateAll() {
  if (!org.value) return
  generatingAll.value = true
  error.value = null
  try {
    const base = useApiBase()
    const res = await fetch(`${base}/organizations/${org.value.id}/deliverable`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: '{}',
    })
    await saveZipBlob(res, org.value.slug)
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    generatingAll.value = false
  }
}

async function generateMember(m: Member) {
  if (!org.value) return
  generatingMemberId.value = m.id
  error.value = null
  try {
    const base = useApiBase()
    const res = await fetch(`${base}/organizations/${org.value.id}/members/${m.id}/deliverable`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: '{}',
    })
    const slug = `${org.value.slug}_${memberName(m).toLowerCase().replaceAll(' ', '-')}`
    await saveZipBlob(res, slug)
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    generatingMemberId.value = null
  }
}

function openSavedFolder() {
  if (savedZipPath.value) openPath(savedZipPath.value).catch(() => {})
}
</script>

<template>
  <UDashboardPanel :id="`organization-${id}`">
    <template #header>
      <UDashboardNavbar :title="org?.name || 'Organisation'">
        <template #leading>
          <div class="flex items-center gap-1">
            <UDashboardSidebarCollapse />
            <UButton to="/organizations" color="neutral" variant="ghost" icon="i-lucide-arrow-left" />
          </div>
        </template>
        <template #right>
          <div class="flex items-center gap-2">
            <span v-if="org" class="text-muted hidden text-xs sm:inline">
              {{ org.members.length }} membres · {{ signatureCount }} signatures
            </span>
            <UButton
              color="primary"
              variant="solid"
              icon="i-lucide-package-check"
              :loading="generatingAll"
              :disabled="!org || signatureCount === 0"
              @click="generateAll"
            >
              Générer tout ({{ signatureCount }})
            </UButton>
          </div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="space-y-4 p-4 sm:p-6">
        <UAlert v-if="error" color="red" variant="soft" title="Erreur" :description="error" />
        <div v-if="loading" class="text-muted text-sm">Chargement…</div>

        <template v-else-if="org">
          <UAlert
            v-if="generatingAll"
            color="primary"
            variant="soft"
            icon="i-lucide-loader"
            title="Génération en cours…"
            :description="`Création des ${signatureCount} signatures (HTML, images, Apple Mail). Cela peut prendre 1 à 2 minutes.`"
          />

          <!-- ============ OPTION : LOGO CHAMBERS ============ -->
          <UCard>
            <div class="flex flex-wrap items-center justify-between gap-4">
              <div class="min-w-0">
                <div class="flex items-center gap-2 font-medium">
                  <UIcon name="i-lucide-image" class="size-4" />
                  Logo Chambers (2ᵉ image)
                </div>
                <p class="text-muted mt-1 text-xs leading-relaxed">
                  Affiché sous le logo LEXIAL, sur toute la largeur. À garder <b>masqué</b> tant que l'image
                  définitive n'est pas reçue — le 25 juin, dépose la vraie image, active l'option, puis « Générer tout ».
                </p>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-muted text-xs">{{ org.show_chambers ? 'Affiché' : 'Masqué' }}</span>
                <USwitch :model-value="org.show_chambers" @update:model-value="setShowChambers" />
              </div>
            </div>
          </UCard>

          <!-- ============ OPTION : TÉLÉPHONE ============ -->
          <UCard>
            <div class="flex flex-wrap items-center justify-between gap-4">
              <div class="min-w-0">
                <div class="flex items-center gap-2 font-medium">
                  <UIcon name="i-lucide-phone" class="size-4" />
                  Téléphone dans la signature
                </div>
                <p class="text-muted mt-1 text-xs leading-relaxed">
                  Masqué par défaut (LEXIAL a retiré le téléphone au profit des villes cliquables). Activez-le
                  pour afficher le numéro du bureau à la suite des villes, puis « Générer tout ».
                </p>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-muted text-xs">{{ org.show_phone ? 'Affiché' : 'Masqué' }}</span>
                <USwitch :model-value="org.show_phone" @update:model-value="setShowPhone" />
              </div>
            </div>
          </UCard>

          <!-- ============ BUREAUX ============ -->
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <div class="font-semibold">Bureaux</div>
                <UBadge color="neutral" variant="soft">{{ org.offices.length }}</UBadge>
              </div>
            </template>

            <div class="space-y-2">
              <div
                v-for="o in org.offices"
                :key="o.id"
                class="ring-default flex flex-wrap items-center justify-between gap-2 rounded-lg px-3 py-2 ring-1"
              >
                <div class="min-w-0">
                  <span class="font-medium">{{ o.label }}</span>
                  <span class="text-muted ml-2 text-xs">{{ templateTitle(o.template_key) }}</span>
                </div>
                <UButton
                  size="xs"
                  color="error"
                  variant="ghost"
                  icon="i-lucide-trash-2"
                  title="Supprimer le bureau"
                  @click="deleteOffice(o.id)"
                />
              </div>
              <p v-if="org.offices.length === 0" class="text-muted text-sm">
                Aucun bureau. Ajoute Paris / Genève / Bruxelles ci-dessous.
              </p>
            </div>

            <template #footer>
              <div class="flex flex-wrap items-end gap-2">
                <UFormField label="Libellé du bureau" class="min-w-0 flex-1">
                  <UInput v-model="newOffice.label" class="w-full" placeholder="Paris" />
                </UFormField>
                <UFormField label="Template" class="min-w-0 flex-1">
                  <USelect
                    v-model="newOffice.template_key"
                    class="w-full"
                    :items="templateItems"
                    :ui="{ content: 'z-[350] max-h-72' }"
                  />
                </UFormField>
                <UButton
                  color="neutral"
                  variant="soft"
                  icon="i-lucide-plus"
                  :loading="addingOffice"
                  :disabled="!newOffice.label.trim() || !newOffice.template_key"
                  @click="addOffice"
                >
                  Ajouter
                </UButton>
              </div>
            </template>
          </UCard>

          <!-- ============ MEMBRES ============ -->
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <div class="font-semibold">Membres</div>
                <UButton color="neutral" variant="soft" size="sm" icon="i-lucide-user-plus" @click="openCreateMember">
                  Ajouter un membre
                </UButton>
              </div>
            </template>

            <div class="space-y-2">
              <div
                v-for="m in org.members"
                :key="m.id"
                class="ring-default flex flex-wrap items-center gap-3 rounded-lg px-3 py-2 ring-1"
              >
                <div class="min-w-0 flex-1">
                  <div class="truncate font-medium">{{ memberName(m) }}</div>
                  <div class="text-muted truncate text-xs">{{ m.title || '—' }}</div>
                </div>
                <div class="flex flex-wrap gap-1">
                  <UBadge v-for="o in m.offices" :key="o.id" color="neutral" variant="soft" size="sm">
                    {{ o.label }}
                  </UBadge>
                  <UBadge v-if="m.offices.length === 0" color="warning" variant="soft" size="sm">
                    aucun bureau
                  </UBadge>
                </div>
                <div class="flex shrink-0 items-center gap-1">
                  <UButton
                    size="xs"
                    color="primary"
                    variant="soft"
                    icon="i-lucide-download"
                    :loading="generatingMemberId === m.id"
                    :disabled="m.offices.length === 0 || generatingAll"
                    title="Générer ses signatures"
                    @click="generateMember(m)"
                  >
                    Générer
                  </UButton>
                  <UButton
                    size="xs"
                    color="neutral"
                    variant="ghost"
                    icon="i-lucide-pencil"
                    title="Modifier"
                    @click="openEditMember(m)"
                  />
                  <UButton
                    size="xs"
                    color="error"
                    variant="ghost"
                    icon="i-lucide-trash-2"
                    title="Supprimer"
                    @click="deleteMember(m.id)"
                  />
                </div>
              </div>
              <p v-if="org.members.length === 0" class="text-muted text-sm">
                Aucun membre. Clique « Ajouter un membre ».
              </p>
            </div>
          </UCard>
        </template>
      </div>
    </template>
  </UDashboardPanel>

  <!-- ===== Modal membre ===== -->
  <UModal
    v-model:open="memberModalOpen"
    :title="memberDraft.id == null ? 'Ajouter un membre' : 'Modifier le membre'"
    description="Nom + titre + bureaux. Le nom et le titre apparaissent dans la signature."
    class="sm:max-w-lg"
  >
    <template #body>
      <div class="space-y-4">
        <div class="grid gap-3 sm:grid-cols-2">
          <UFormField label="Prénom">
            <UInput v-model="memberDraft.firstname" class="w-full" placeholder="Emmanuel" />
          </UFormField>
          <UFormField label="Nom">
            <UInput v-model="memberDraft.lastname" class="w-full" placeholder="Ruchat" />
          </UFormField>
        </div>
        <UFormField label="Titre / fonction">
          <UInput v-model="memberDraft.title" class="w-full" placeholder="Associé – Partner" />
        </UFormField>
        <UFormField label="Bureaux">
          <div v-if="org && org.offices.length" class="flex flex-wrap gap-3 pt-1">
            <UCheckbox
              v-for="o in org.offices"
              :key="o.id"
              :model-value="memberDraft.office_ids.includes(o.id)"
              :label="o.label"
              @update:model-value="(v: boolean) => toggleDraftOffice(o.id, v)"
            />
          </div>
          <p v-else class="text-muted text-xs">Ajoute d'abord des bureaux à l'organisation.</p>
        </UFormField>
      </div>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton color="neutral" variant="ghost" @click="memberModalOpen = false">Annuler</UButton>
        <UButton color="primary" :loading="savingMember" @click="saveMember">Enregistrer</UButton>
      </div>
    </template>
  </UModal>

  <SignDexDeliverablePathModal v-model:open="deliverablePathModalOpen" :path="savedZipPath" />
</template>
