<template>
  <UDashboardPanel id="configuration" :ui="{ body: 'p-3 sm:p-6 bg-neutral-100 dark:bg-transparent' }">
    <template #header>
      <UDashboardNavbar title="Configuration">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <UButton icon="i-lucide-refresh-cw" color="neutral" variant="ghost" :loading="loading" @click="load" />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="w-full space-y-10 pb-6">
        <UAlert v-if="error" color="error" variant="soft" icon="i-lucide-triangle-alert" title="Erreur" :description="error" />

        <!-- Images de la signature (en premier) -->
        <section>
          <h2 class="text-highlighted text-base font-semibold">Images de la signature</h2>
          <p class="text-muted mb-4 mt-1 text-sm">Communes à toutes les signatures. Laissez « par défaut » pour garder les images d'origine.</p>

          <div class="grid gap-4 sm:grid-cols-2">
            <div v-for="img in images" :key="img.field" class="flex items-center gap-4 rounded-2xl p-4" :class="cardClass">
              <span class="ring-default flex h-14 w-24 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-white ring-1">
                <img v-if="img.url.value" :src="img.url.value" :alt="img.title" class="max-h-12 max-w-20 object-contain">
                <UIcon v-else name="i-lucide-image-off" class="text-dimmed size-5" />
              </span>
              <div class="min-w-0 flex-1">
                <p class="text-highlighted text-sm font-medium">{{ img.title }}</p>
                <p class="text-muted text-xs">{{ img.isDefault.value ? 'Image par défaut' : 'Personnalisée' }}</p>
                <div class="mt-2 flex gap-1.5">
                  <input :ref="img.inputRef" type="file" accept="image/*" class="hidden" @change="(e) => onImage(img.field, e)">
                  <UButton size="xs" color="neutral" variant="soft" icon="i-lucide-upload" :loading="uploading === img.field" label="Modifier" @click="pick(img.field)" />
                  <UButton v-if="!img.isDefault.value" size="xs" color="neutral" variant="ghost" label="Réinitialiser" @click="resetImage(img.field)" />
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Bureaux (accordéon) -->
        <section>
          <div class="mb-1 flex flex-wrap items-center justify-between gap-3">
            <h2 class="text-highlighted text-base font-semibold">Bureaux</h2>
            <UButton icon="i-lucide-plus" color="neutral" :style="brandButtonStyle" label="Ajouter un bureau" @click="openAddOffice" />
          </div>
          <p class="text-muted mb-4 text-sm">Dépliez un bureau pour modifier son adresse (déménagement). Les signatures rattachées seront à jour au prochain téléchargement.</p>

          <div v-if="loading" class="space-y-2">
            <USkeleton v-for="i in 3" :key="i" class="h-16 w-full rounded-2xl bg-neutral-200 dark:bg-neutral-800" />
          </div>
          <div v-else class="space-y-2.5">
            <UCollapsible
              v-for="d in drafts"
              :key="d.id"
              :open="openOfficeId === d.id"
              class="overflow-hidden rounded-2xl"
              :class="cardClass"
              @update:open="(v: boolean) => { openOfficeId = v ? d.id : null }"
            >
              <template #default="{ open }">
                <button type="button" class="flex w-full items-center justify-between gap-3 p-4 text-left">
                  <span class="min-w-0">
                    <span class="text-highlighted flex items-center gap-2 font-medium">
                      <UIcon name="i-lucide-map-pin" class="size-4 shrink-0" :style="{ color: pinColor(d.label) }" />{{ d.label }}
                    </span>
                    <span class="text-muted mt-0.5 block truncate text-xs">{{ [d.address_street, d.address_cp_city].filter(Boolean).join(', ') || 'Adresse à compléter' }}</span>
                  </span>
                  <UIcon name="i-lucide-chevron-down" class="text-muted size-5 shrink-0 transition-transform" :class="open ? 'rotate-180' : ''" />
                </button>
              </template>
              <template #content>
                <div class="border-default space-y-3 border-t p-4">
                  <UFormField label="Nom du bureau">
                    <UInput v-model="d.label" class="w-full" />
                  </UFormField>
                  <div class="grid gap-3 sm:grid-cols-2">
                    <UFormField label="Rue">
                      <UInput v-model="d.address_street" placeholder="30 rue Jouffroy d’Abbans" class="w-full" />
                    </UFormField>
                    <UFormField label="Code postal + ville">
                      <UInput v-model="d.address_cp_city" placeholder="F-75017 Paris" class="w-full" />
                    </UFormField>
                    <UFormField label="Téléphone">
                      <UInput v-model="d.phone_display" placeholder="+33 1 84 60 60 16" class="w-full" />
                    </UFormField>
                  </div>
                  <div class="flex justify-end">
                    <UButton size="sm" color="neutral" :style="brandButtonStyle" icon="i-lucide-save" :loading="savingOfficeId === d.id" label="Enregistrer" @click="saveOffice(d)" />
                  </div>
                </div>
              </template>
            </UCollapsible>
          </div>
        </section>
      </div>
    </template>
  </UDashboardPanel>

  <!-- Ajouter un bureau -->
  <USlideover v-model:open="addOpen" title="Ajouter un bureau">
    <template #body>
      <div class="space-y-4">
        <UFormField label="Nom du bureau">
          <UInput v-model="newOffice.label" placeholder="Lyon" class="w-full" />
        </UFormField>
        <UFormField label="Rue">
          <UInput v-model="newOffice.address_street" class="w-full" />
        </UFormField>
        <UFormField label="Code postal + ville">
          <UInput v-model="newOffice.address_cp_city" class="w-full" />
        </UFormField>
        <UFormField label="Téléphone">
          <UInput v-model="newOffice.phone_display" placeholder="+33 1 84 60 60 16" class="w-full" />
        </UFormField>
      </div>
    </template>
    <template #footer>
      <div class="ml-auto flex gap-2">
        <UButton color="neutral" variant="ghost" label="Annuler" @click="addOpen = false" />
        <UButton icon="i-lucide-plus" color="neutral" :style="brandButtonStyle" :loading="addingOffice" :disabled="!newOffice.label.trim()" label="Ajouter" @click="addOffice" />
      </div>
    </template>
  </USlideover>
</template>

<script setup lang="ts">
import type { ComputedRef, Ref } from 'vue'
import type { PortalOverview } from '~/types/portal'

definePageMeta({ layout: 'portal' })
useHead({ title: 'Configuration' })

const toast = useToast()
const { brandButtonStyle } = useBrand()

const cardClass = 'bg-default ring-1 ring-default shadow-sm dark:bg-elevated/60 dark:shadow-none'

const DEFAULT_LOGO = 'https://aapjpybdkzqtgxavjjem.supabase.co/storage/v1/object/public/GoupixDex/template-assets/lexial/lexial-logo-transparent.png'
const DEFAULT_CHAMBERS = 'https://aapjpybdkzqtgxavjjem.supabase.co/storage/v1/object/public/GoupixDex/template-assets/lexial/chambers-2026.png'

interface OfficeDraft {
  id: number
  label: string
  address_street: string
  address_cp_city: string
  phone_display: string
}

// SSR : données récupérées côté serveur → page déjà remplie au reload (pas de skeleton).
const { data: overview, status, error: overviewError, refresh } = await useAsyncData<PortalOverview>(
  'portal-overview',
  () => apiFetch<PortalOverview>('/portal/overview'),
)
const loading: ComputedRef<boolean> = computed(() => status.value === 'pending')
const error: ComputedRef<string | null> = computed(() =>
  overviewError.value ? (overviewError.value.message || 'Chargement impossible') : null,
)
const drafts = ref<OfficeDraft[]>([])
const savingOfficeId = ref<number | null>(null)
const openOfficeId = ref<number | null>(null)

const sigLogoUrl = ref<string | null>(null)
const sigChambersUrl = ref<string | null>(null)
const uploading = ref<string | null>(null)
const logoInput = ref<HTMLInputElement | null>(null)
const chambersInput = ref<HTMLInputElement | null>(null)

const addOpen = ref(false)
const addingOffice = ref(false)
const newOffice = reactive({ label: '', address_street: '', address_cp_city: '', phone_display: '' })

const logoEffective: ComputedRef<string> = computed(() => sigLogoUrl.value || DEFAULT_LOGO)
const chambersEffective: ComputedRef<string> = computed(() => sigChambersUrl.value || DEFAULT_CHAMBERS)
const logoIsDefault: ComputedRef<boolean> = computed(() => !sigLogoUrl.value)
const chambersIsDefault: ComputedRef<boolean> = computed(() => !sigChambersUrl.value)

const images: ComputedRef<{ field: 'logo' | 'chambers', title: string, url: Ref<string>, isDefault: Ref<boolean>, inputRef: Ref<HTMLInputElement | null> }[]> = computed(() => [
  { field: 'logo', title: 'Logo de la signature', url: logoEffective, isDefault: logoIsDefault, inputRef: logoInput },
  { field: 'chambers', title: 'Image Chambers', url: chambersEffective, isDefault: chambersIsDefault, inputRef: chambersInput },
])

function pinColor(label: string): string {
  const k = (label || '').toLowerCase()
  if (k.includes('paris')) return '#0ea5e9'
  if (k.includes('gen')) return '#22c55e'
  if (k.includes('brux') || k.includes('brus')) return '#f59e0b'
  const palette = ['#0ea5e9', '#22c55e', '#f59e0b', '#a855f7', '#ec4899', '#14b8a6']
  let s = 0
  for (const c of k) s += c.charCodeAt(0)
  return palette[s % palette.length]!
}

/** Remplit les brouillons éditables + images à partir des données chargées (SSR au montage + refresh). */
function populateFromOverview(data: PortalOverview | null): void {
  if (!data) return
  drafts.value = data.offices.map(o => ({
    id: o.id,
    label: o.label,
    address_street: o.address_street || '',
    address_cp_city: o.address_cp_city || '',
    phone_display: o.phone_display || '',
  }))
  openOfficeId.value = drafts.value[0]?.id ?? null
  sigLogoUrl.value = data.organization.sig_logo_url
  sigChambersUrl.value = data.organization.sig_chambers_url
}
watch(overview, populateFromOverview, { immediate: true })

async function load(): Promise<void> {
  await refresh()
}

async function saveOffice(d: OfficeDraft): Promise<void> {
  savingOfficeId.value = d.id
  try {
    await apiFetch(`/portal/offices/${d.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label: d.label, address_street: d.address_street, address_cp_city: d.address_cp_city, phone_display: d.phone_display }),
    })
    toast.add({ title: 'Bureau enregistré', color: 'success', icon: 'i-lucide-check' })
  } catch (e) {
    toast.add({ title: 'Enregistrement impossible', description: (e as Error).message, color: 'error' })
  } finally {
    savingOfficeId.value = null
  }
}

function openAddOffice(): void {
  newOffice.label = ''
  newOffice.address_street = ''
  newOffice.address_cp_city = ''
  newOffice.phone_display = ''
  addOpen.value = true
}

async function addOffice(): Promise<void> {
  if (!newOffice.label.trim()) return
  addingOffice.value = true
  try {
    await apiFetch('/portal/offices', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...newOffice }) })
    addOpen.value = false
    await load()
    toast.add({ title: 'Bureau ajouté', color: 'success', icon: 'i-lucide-check' })
  } catch (e) {
    toast.add({ title: 'Ajout impossible', description: (e as Error).message, color: 'error' })
  } finally {
    addingOffice.value = false
  }
}

function pick(field: 'logo' | 'chambers'): void {
  if (field === 'logo') logoInput.value?.click()
  else chambersInput.value?.click()
}

async function onImage(field: 'logo' | 'chambers', event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploading.value = field
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await apiFetch<{ field: string, url: string }>(`/portal/signature-image?field=${field}`, { method: 'POST', body: fd })
    if (field === 'logo') sigLogoUrl.value = res.url
    else sigChambersUrl.value = res.url
    toast.add({ title: 'Image mise à jour', color: 'success', icon: 'i-lucide-check' })
  } catch (e) {
    toast.add({ title: 'Téléversement impossible', description: (e as Error).message, color: 'error' })
  } finally {
    uploading.value = null
    input.value = ''
  }
}

async function resetImage(field: 'logo' | 'chambers'): Promise<void> {
  try {
    await apiFetch(`/portal/signature-image?field=${field}`, { method: 'DELETE' })
    if (field === 'logo') sigLogoUrl.value = null
    else sigChambersUrl.value = null
    toast.add({ title: 'Image réinitialisée', color: 'success' })
  } catch (e) {
    toast.add({ title: 'Action impossible', description: (e as Error).message, color: 'error' })
  }
}

</script>
