<template>
  <UDashboardPanel id="espaces-clients">
    <template #header>
      <UDashboardNavbar title="Espaces clients">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <UButton icon="i-lucide-refresh-cw" color="neutral" variant="ghost" :loading="loadingOrgs" @click="loadOrgs" />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="grid gap-4 p-4 sm:p-6 lg:grid-cols-[300px_1fr]">
        <!-- Colonne gauche : liste des organisations -->
        <div class="space-y-2">
          <UButton
            to="/organizations"
            icon="i-lucide-plus"
            block
            color="neutral"
            variant="subtle"
            label="Créer une organisation"
          />
          <p class="text-muted px-1 text-xs font-medium uppercase tracking-wide">Organisations</p>
          <div v-if="loadingOrgs" class="space-y-2">
            <USkeleton v-for="i in 3" :key="i" class="h-16 w-full" />
          </div>
          <template v-else>
            <button
              v-for="o in orgs"
              :key="o.id"
              type="button"
              class="border-default hover:bg-elevated/50 w-full rounded-lg border p-3 text-left transition-colors"
              :class="o.id === selectedOrgId ? 'border-primary bg-elevated/40' : ''"
              @click="selectOrg(o.id)"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-highlighted truncate font-medium">{{ o.name }}</span>
                <span
                  class="ring-default size-3 shrink-0 rounded-full ring-1"
                  :style="{ backgroundColor: o.brand_color || '#e5e7eb' }"
                />
              </div>
              <div class="text-muted mt-1 text-xs">{{ o.member_count }} membres · {{ o.signature_count }} signatures</div>
            </button>
            <p v-if="!orgs.length" class="text-muted p-3 text-sm">
              Aucune organisation. Créez-en une dans « Organisations ».
            </p>
          </template>
        </div>

        <!-- Colonne droite : détail de l'espace sélectionné -->
        <div v-if="selectedOrg" class="space-y-4">
          <!-- Identité visuelle -->
          <UCard>
            <template #header>
              <div class="flex items-center gap-2">
                <UIcon name="i-lucide-palette" class="text-muted size-4" />
                <span class="font-medium">Identité visuelle — {{ selectedOrg.name }}</span>
              </div>
            </template>
            <div class="grid gap-4 sm:grid-cols-2">
              <UFormField label="Couleur de marque">
                <div class="flex items-center gap-2">
                  <input
                    v-model="branding.brand_color"
                    type="color"
                    class="border-default h-9 w-12 shrink-0 cursor-pointer rounded border bg-transparent"
                  >
                  <UInput v-model="branding.brand_color" placeholder="#001958" class="w-full" />
                </div>
              </UFormField>
              <UFormField label="Logo">
                <div class="flex items-center gap-3">
                  <span
                    v-if="branding.brand_logo_url"
                    class="ring-default flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-white ring-1"
                  >
                    <img :src="branding.brand_logo_url" alt="Logo" class="max-h-9 max-w-9 object-contain">
                  </span>
                  <input ref="logoInput" type="file" accept="image/*" class="hidden" @change="onLogoSelected">
                  <UButton
                    :label="branding.brand_logo_url ? 'Changer le logo' : 'Téléverser un logo'"
                    icon="i-lucide-upload"
                    color="neutral"
                    variant="soft"
                    :loading="uploadingLogo"
                    @click="logoInput?.click()"
                  />
                  <UButton
                    v-if="branding.brand_logo_url"
                    icon="i-lucide-x"
                    color="neutral"
                    variant="ghost"
                    size="sm"
                    title="Retirer le logo"
                    @click="clearLogo"
                  />
                </div>
              </UFormField>
            </div>
            <UFormField
              label="Thème par défaut de l'espace"
              help="Mode d'affichage à l'ouverture de l'espace client (le client peut ensuite changer)."
              class="mt-4"
            >
              <USelect v-model="branding.default_theme" :items="themeItems" class="w-full sm:w-72" />
            </UFormField>
            <div class="mt-4 flex justify-end">
              <UButton :loading="savingBranding" label="Enregistrer" icon="i-lucide-save" @click="saveBranding" />
            </div>
          </UCard>

          <!-- Accès -->
          <UCard>
            <template #header>
              <div class="flex items-center gap-2">
                <UIcon name="i-lucide-key-round" class="text-muted size-4" />
                <span class="font-medium">Accès ({{ users.length }})</span>
              </div>
            </template>

            <UAlert
              v-if="lastInvite"
              color="primary"
              variant="soft"
              icon="i-lucide-link"
              :title="`Lien d'invitation pour ${lastInvite.user.email}`"
              class="mb-4"
            >
              <template #description>
                <div class="mt-2 flex items-center gap-2">
                  <UInput :model-value="lastInvite.invite_url" readonly size="sm" class="w-full font-mono text-xs" />
                  <UButton icon="i-lucide-copy" size="sm" color="neutral" variant="soft" @click="copy(lastInvite.invite_url)" />
                </div>
                <p class="text-muted mt-1.5 text-xs">
                  Envoyez ce lien à la personne : il lui permet de définir son mot de passe et d'activer son accès.
                </p>
              </template>
            </UAlert>

            <div v-if="loadingUsers" class="space-y-2">
              <USkeleton v-for="i in 2" :key="i" class="h-12 w-full" />
            </div>
            <ul v-else class="divide-default divide-y">
              <li v-for="u in users" :key="u.id" class="flex items-center justify-between gap-3 py-2.5">
                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="text-highlighted truncate text-sm font-medium">{{ u.full_name || u.email }}</span>
                    <UBadge :color="u.role === 'owner' ? 'primary' : 'neutral'" variant="subtle" size="sm">
                      {{ u.role === 'owner' ? 'Propriétaire' : 'Éditeur' }}
                    </UBadge>
                    <UBadge :color="u.status === 'active' ? 'success' : 'warning'" variant="subtle" size="sm">
                      {{ u.status === 'active' ? 'Actif' : 'Invité' }}
                    </UBadge>
                  </div>
                  <div class="text-muted truncate text-xs">{{ u.email }}</div>
                </div>
                <div class="flex shrink-0 items-center gap-1">
                  <UButton
                    icon="i-lucide-link"
                    size="sm"
                    color="neutral"
                    variant="ghost"
                    title="Générer un nouveau lien d'invitation"
                    :loading="busyUserId === u.id"
                    @click="reinvite(u)"
                  />
                  <UButton
                    icon="i-lucide-trash-2"
                    size="sm"
                    color="error"
                    variant="ghost"
                    title="Supprimer l'accès"
                    @click="removeAccess(u)"
                  />
                </div>
              </li>
              <li v-if="!users.length" class="text-muted py-3 text-sm">Aucun accès pour cet espace.</li>
            </ul>

            <USeparator class="my-4" />

            <UForm :state="newAccess" :validate="validateAccess" class="space-y-3" @submit="createAccess">
              <p class="text-highlighted text-sm font-medium">Ajouter un accès</p>
              <div class="grid gap-3 sm:grid-cols-2">
                <UFormField label="Email" name="email">
                  <UInput v-model="newAccess.email" type="email" placeholder="prenom@cabinet.com" class="w-full" />
                </UFormField>
                <UFormField label="Nom (optionnel)" name="full_name">
                  <UInput v-model="newAccess.full_name" placeholder="Emmanuel Ruchat" class="w-full" />
                </UFormField>
              </div>
              <UFormField label="Rôle" name="role">
                <USelect v-model="newAccess.role" :items="roleItems" class="w-full sm:w-72" />
              </UFormField>
              <div class="flex justify-end">
                <UButton type="submit" :loading="creatingAccess" icon="i-lucide-user-plus" label="Créer l'accès + lien" />
              </div>
            </UForm>
          </UCard>
        </div>

        <div
          v-else
          class="border-default text-muted flex items-center justify-center rounded-lg border border-dashed p-10 text-sm"
        >
          Sélectionnez une organisation pour gérer ses accès.
        </div>
      </div>
    </template>
  </UDashboardPanel>
</template>

<script setup lang="ts">
import type { FormError } from '@nuxt/ui'
import type { AccessUser, InviteLink, UserRole } from '~/types/auth'

interface OrgSummary {
  id: number
  name: string
  brand_color: string | null
  brand_logo_url: string | null
  default_theme: string | null
  member_count: number
  signature_count: number
}

useHead({ title: 'Espaces clients — SignDex' })
const toast = useToast()

const orgs = ref<OrgSummary[]>([])
const loadingOrgs = ref(false)
const selectedOrgId = ref<number | null>(null)
const selectedOrg = computed<OrgSummary | null>(
  () => orgs.value.find(o => o.id === selectedOrgId.value) || null,
)

const users = ref<AccessUser[]>([])
const loadingUsers = ref(false)
const busyUserId = ref<number | null>(null)

const branding = reactive<{ brand_color: string, brand_logo_url: string, default_theme: string }>({ brand_color: '#001958', brand_logo_url: '', default_theme: 'system' })
const savingBranding = ref(false)
const logoInput = ref<HTMLInputElement | null>(null)
const uploadingLogo = ref(false)

const newAccess = reactive<{ email: string, full_name: string, role: UserRole }>({ email: '', full_name: '', role: 'owner' })
const creatingAccess = ref(false)
const lastInvite = ref<InviteLink | null>(null)

const roleItems = [
  { label: 'Propriétaire (gère les accès + contenu)', value: 'owner' },
  { label: 'Éditeur (contenu uniquement)', value: 'editor' },
]

const themeItems = [
  { label: 'Automatique (système)', value: 'system' },
  { label: 'Clair', value: 'light' },
  { label: 'Sombre', value: 'dark' },
]

function humanError(e: unknown): string {
  const msg = String((e as Error)?.message || e)
  const m = msg.match(/"detail":"([^"]+)"/)
  return m?.[1] || msg
}

async function loadOrgs(): Promise<void> {
  loadingOrgs.value = true
  try {
    orgs.value = await apiFetch<OrgSummary[]>('/organizations')
    if (!selectedOrgId.value && orgs.value.length) await selectOrg(orgs.value[0]!.id)
  } catch (e) {
    toast.add({ title: 'Chargement impossible', description: humanError(e), color: 'error' })
  } finally {
    loadingOrgs.value = false
  }
}

async function selectOrg(id: number): Promise<void> {
  selectedOrgId.value = id
  lastInvite.value = null
  const o = orgs.value.find(x => x.id === id)
  branding.brand_color = o?.brand_color || '#001958'
  branding.brand_logo_url = o?.brand_logo_url || ''
  branding.default_theme = o?.default_theme || 'system'
  await loadUsers()
}

async function loadUsers(): Promise<void> {
  if (!selectedOrgId.value) return
  loadingUsers.value = true
  try {
    users.value = await apiFetch<AccessUser[]>(`/organizations/${selectedOrgId.value}/users`)
  } catch (e) {
    toast.add({ title: 'Accès illisibles', description: humanError(e), color: 'error' })
  } finally {
    loadingUsers.value = false
  }
}

/** 'system' → null (aucun thème forcé) ; sinon la valeur choisie. */
function brandingTheme(): string | null {
  return branding.default_theme === 'system' ? null : (branding.default_theme || null)
}

async function saveBranding(): Promise<void> {
  if (!selectedOrgId.value) return
  savingBranding.value = true
  try {
    await apiFetch(`/organizations/${selectedOrgId.value}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        brand_color: branding.brand_color || null,
        brand_logo_url: branding.brand_logo_url || null,
        default_theme: brandingTheme(),
      }),
    })
    const o = orgs.value.find(x => x.id === selectedOrgId.value)
    if (o) {
      o.brand_color = branding.brand_color || null
      o.brand_logo_url = branding.brand_logo_url || null
      o.default_theme = brandingTheme()
    }
    toast.add({ title: 'Identité enregistrée', color: 'success', icon: 'i-lucide-check' })
  } catch (e) {
    toast.add({ title: 'Enregistrement impossible', description: humanError(e), color: 'error' })
  } finally {
    savingBranding.value = false
  }
}

async function onLogoSelected(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !selectedOrgId.value) return
  uploadingLogo.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    const res = await apiFetch<{ brand_logo_url: string }>(
      `/organizations/${selectedOrgId.value}/brand-logo`,
      { method: 'POST', body: form },
    )
    branding.brand_logo_url = res.brand_logo_url
    const o = orgs.value.find(x => x.id === selectedOrgId.value)
    if (o) o.brand_logo_url = res.brand_logo_url
    toast.add({ title: 'Logo téléversé', color: 'success', icon: 'i-lucide-check' })
  } catch (e) {
    toast.add({ title: 'Téléversement impossible', description: humanError(e), color: 'error' })
  } finally {
    uploadingLogo.value = false
    input.value = ''
  }
}

async function clearLogo(): Promise<void> {
  branding.brand_logo_url = ''
  await saveBranding()
}

function validateAccess(s: typeof newAccess): FormError[] {
  const errors: FormError[] = []
  if (!s.email || !s.email.includes('@')) errors.push({ name: 'email', message: 'Email valide requis' })
  return errors
}

async function createAccess(): Promise<void> {
  if (!selectedOrgId.value) return
  creatingAccess.value = true
  try {
    const res = await apiFetch<InviteLink>(`/organizations/${selectedOrgId.value}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: newAccess.email.trim().toLowerCase(),
        full_name: newAccess.full_name.trim() || null,
        role: newAccess.role,
      }),
    })
    lastInvite.value = res
    newAccess.email = ''
    newAccess.full_name = ''
    await loadUsers()
    toast.add({ title: 'Accès créé', description: 'Copiez le lien d\'invitation ci-dessus.', color: 'success', icon: 'i-lucide-check' })
  } catch (e) {
    toast.add({ title: 'Création impossible', description: humanError(e), color: 'error' })
  } finally {
    creatingAccess.value = false
  }
}

async function reinvite(u: AccessUser): Promise<void> {
  if (!selectedOrgId.value) return
  busyUserId.value = u.id
  try {
    const res = await apiFetch<InviteLink>(`/organizations/${selectedOrgId.value}/users/${u.id}/reinvite`, { method: 'POST' })
    lastInvite.value = res
    await loadUsers()
    toast.add({ title: 'Nouveau lien généré', color: 'success', icon: 'i-lucide-link' })
  } catch (e) {
    toast.add({ title: 'Impossible de générer le lien', description: humanError(e), color: 'error' })
  } finally {
    busyUserId.value = null
  }
}

async function removeAccess(u: AccessUser): Promise<void> {
  if (!selectedOrgId.value) return
  if (!confirm(`Supprimer l'accès de ${u.email} ?`)) return
  try {
    await apiFetch(`/organizations/${selectedOrgId.value}/users/${u.id}`, { method: 'DELETE' })
    if (lastInvite.value?.user.id === u.id) lastInvite.value = null
    await loadUsers()
    toast.add({ title: 'Accès supprimé', color: 'success' })
  } catch (e) {
    toast.add({ title: 'Suppression impossible', description: humanError(e), color: 'error' })
  }
}

async function copy(text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text)
    toast.add({ title: 'Lien copié', color: 'success', icon: 'i-lucide-copy' })
  } catch {
    toast.add({ title: 'Copie impossible', color: 'error' })
  }
}

onMounted(loadOrgs)
</script>
