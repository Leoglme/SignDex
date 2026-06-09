<script setup lang="ts">
type OrganizationSummary = {
  id: number
  name: string
  slug: string
  notes?: string | null
  office_count: number
  member_count: number
  signature_count: number
}

const orgs = ref<OrganizationSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const createOpen = ref(false)
const creating = ref(false)
const newOrg = reactive({ name: '', notes: '' })

async function refresh() {
  loading.value = true
  error.value = null
  try {
    orgs.value = await apiFetch<OrganizationSummary[]>('/organizations')
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

async function createOrganization() {
  if (!newOrg.name.trim()) return
  creating.value = true
  error.value = null
  try {
    const created = await apiFetch<{ id: number }>('/organizations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: newOrg.name.trim(),
        notes: newOrg.notes.trim() || null,
      }),
    })
    createOpen.value = false
    newOrg.name = ''
    newOrg.notes = ''
    await navigateTo(`/organizations/${created.id}`)
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    creating.value = false
  }
}

await refresh()
</script>

<template>
  <UDashboardPanel id="organizations">
    <template #header>
      <UDashboardNavbar title="Organisations">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <div class="flex items-center gap-2">
            <UButton color="neutral" variant="soft" icon="i-lucide-plus" @click="createOpen = true">
              Nouvelle organisation
            </UButton>
            <UButton icon="i-lucide-refresh-cw" color="neutral" variant="ghost" :loading="loading" @click="refresh" />
          </div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="space-y-4 p-4 sm:p-6">
        <UAlert v-if="error" color="red" variant="soft" title="Erreur API" :description="error" />

        <UModal
          v-model:open="createOpen"
          title="Créer une organisation"
          description="Ex. un cabinet, une agence. Tu ajouteras ensuite les bureaux et les membres."
          class="sm:max-w-lg"
        >
          <template #body>
            <div class="space-y-4">
              <UFormField label="Nom de l'organisation" required>
                <UInput v-model="newOrg.name" class="w-full" placeholder="LEXIAL" autofocus />
              </UFormField>
              <UFormField label="Notes (optionnel)">
                <UInput v-model="newOrg.notes" class="w-full" placeholder="Cabinet d'avocats — lexial.eu" />
              </UFormField>
            </div>
          </template>
          <template #footer>
            <div class="flex w-full justify-end gap-2">
              <UButton color="neutral" variant="ghost" @click="createOpen = false">Annuler</UButton>
              <UButton color="primary" :loading="creating" :disabled="!newOrg.name.trim()" @click="createOrganization">
                Créer
              </UButton>
            </div>
          </template>
        </UModal>

        <UCard v-if="!loading && orgs.length === 0">
          <div class="text-muted text-sm">
            Aucune organisation. Crée-en une pour regrouper des membres par bureau et générer
            toutes leurs signatures en un clic.
          </div>
        </UCard>

        <div v-else class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <UCard v-for="o in orgs" :key="o.id" class="transition hover:ring-primary">
            <template #header>
              <div class="flex items-center gap-3">
                <div class="bg-primary/10 text-primary flex size-10 shrink-0 items-center justify-center rounded-lg">
                  <UIcon name="i-lucide-building-2" class="size-5" />
                </div>
                <div class="min-w-0">
                  <div class="truncate font-semibold">{{ o.name }}</div>
                  <div v-if="o.notes" class="text-muted truncate text-xs">{{ o.notes }}</div>
                </div>
              </div>
            </template>

            <div class="flex flex-wrap gap-2 text-xs">
              <UBadge color="neutral" variant="soft">{{ o.office_count }} bureaux</UBadge>
              <UBadge color="neutral" variant="soft">{{ o.member_count }} membres</UBadge>
              <UBadge color="primary" variant="soft">{{ o.signature_count }} signatures</UBadge>
            </div>

            <template #footer>
              <div class="flex justify-end">
                <UButton :to="`/organizations/${o.id}`" color="primary" variant="soft">Ouvrir</UButton>
              </div>
            </template>
          </UCard>
        </div>
      </div>
    </template>
  </UDashboardPanel>
</template>
