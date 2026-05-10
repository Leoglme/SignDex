<script setup lang="ts">
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

const clients = ref<Client[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const createOpen = ref(false)
const creating = ref(false)
function emptyToNull(s: string): string | null {
  const t = s.trim()
  return t ? t : null
}

const newClient = reactive({
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

async function refresh() {
  loading.value = true
  error.value = null
  try {
    clients.value = await apiFetch<Client[]>('/clients')
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

async function createClient() {
  creating.value = true
  error.value = null
  try {
    await apiFetch<Client>('/clients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: newClient.name.trim(),
        subtitle: emptyToNull(newClient.subtitle),
        firstname: emptyToNull(newClient.firstname),
        lastname: emptyToNull(newClient.lastname),
        website_url: emptyToNull(newClient.website_url),
        email: emptyToNull(newClient.email),
        phone_primary: emptyToNull(newClient.phone_primary),
        phone_secondary: emptyToNull(newClient.phone_secondary),
        linkedin_url: emptyToNull(newClient.linkedin_url),
        instagram_url: emptyToNull(newClient.instagram_url),
        facebook_url: emptyToNull(newClient.facebook_url),
        tiktok_url: emptyToNull(newClient.tiktok_url),
        youtube_url: emptyToNull(newClient.youtube_url),
        color_primary: emptyToNull(newClient.color_primary),
        color_secondary: emptyToNull(newClient.color_secondary),
        logo_url: emptyToNull(newClient.logo_url),
        photo1_url: emptyToNull(newClient.photo1_url),
        photo2_url: emptyToNull(newClient.photo2_url),
        notes: emptyToNull(newClient.notes),
      }),
    })
    createOpen.value = false
    Object.assign(newClient, {
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
    await refresh()
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    creating.value = false
  }
}

await refresh()
</script>

<template>
  <UDashboardPanel id="clients">
    <template #header>
      <UDashboardNavbar title="Clients">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <div class="flex items-center gap-2">
            <UButton to="/templates" color="neutral" variant="ghost" icon="i-lucide-layout-template" />
            <UButton to="/deliverables" color="neutral" variant="ghost" icon="i-lucide-package" />
            <UButton color="neutral" variant="soft" icon="i-lucide-plus" @click="createOpen = true">
              Nouveau
            </UButton>
            <UButton icon="i-lucide-refresh-cw" color="neutral" variant="ghost" :loading="loading" @click="refresh" />
          </div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="space-y-4 p-4 sm:p-6">
        <UAlert v-if="error" color="red" variant="soft" title="Erreur API" :description="error" />

        <!-- Nuxt UI v4 : le slot default = trigger uniquement ; le contenu va dans #body / #footer -->
        <UModal
          v-model:open="createOpen"
          title="Créer un client"
          description="Renseigne les infos du client (tu pourras compléter sur la fiche)."
          class="sm:max-w-3xl"
        >
          <template #body>
            <div class="max-h-[min(72vh,560px)] overflow-y-auto">
              <div class="grid min-w-0 gap-4 sm:grid-cols-2">
                <UFormField label="Nom de l'entreprise" hint="Sert d'identifiant et de marque sur les supports." class="min-w-0 sm:col-span-2">
                  <UInput v-model="newClient.name" class="w-full" placeholder="HelloPropre" />
                </UFormField>
                <UFormField label="Prénom (contact)" class="min-w-0">
                  <UInput v-model="newClient.firstname" class="w-full" placeholder="Aihaht" />
                </UFormField>
                <UFormField label="Nom (contact)" class="min-w-0">
                  <UInput v-model="newClient.lastname" class="w-full" placeholder="EDANH" />
                </UFormField>
                <UFormField label="Sous-titre / slogan" class="min-w-0 sm:col-span-2">
                  <UInput v-model="newClient.subtitle" class="w-full" placeholder="Service de nettoyage professionnel" />
                </UFormField>
                <UFormField label="Site web" class="min-w-0">
                  <UInput v-model="newClient.website_url" class="w-full" placeholder="https://…" />
                </UFormField>
                <UFormField label="Email" class="min-w-0">
                  <UInput v-model="newClient.email" class="w-full" placeholder="contact@…" />
                </UFormField>
                <UFormField label="Téléphone 1" class="min-w-0">
                  <UInput v-model="newClient.phone_primary" class="w-full" placeholder="06…" />
                </UFormField>
                <UFormField label="Téléphone 2" class="min-w-0">
                  <UInput v-model="newClient.phone_secondary" class="w-full" placeholder="06…" />
                </UFormField>
                <UFormField label="LinkedIn" class="min-w-0 sm:col-span-2">
                  <UInput v-model="newClient.linkedin_url" class="w-full" placeholder="https://linkedin.com/…" />
                </UFormField>
                <UFormField label="Instagram" class="min-w-0">
                  <UInput v-model="newClient.instagram_url" class="w-full" placeholder="https://…" />
                </UFormField>
                <UFormField label="Facebook" class="min-w-0">
                  <UInput v-model="newClient.facebook_url" class="w-full" placeholder="https://…" />
                </UFormField>
                <UFormField label="TikTok" class="min-w-0">
                  <UInput v-model="newClient.tiktok_url" class="w-full" placeholder="https://…" />
                </UFormField>
                <UFormField label="YouTube" class="min-w-0">
                  <UInput v-model="newClient.youtube_url" class="w-full" placeholder="https://…" />
                </UFormField>
                <UFormField label="Couleur 1" class="min-w-0">
                  <UInput v-model="newClient.color_primary" class="w-full" placeholder="#4e8baa" />
                </UFormField>
                <UFormField label="Couleur 2" class="min-w-0">
                  <UInput v-model="newClient.color_secondary" class="w-full" placeholder="#5a9abf" />
                </UFormField>
                <UFormField label="Logo (URL)" hint="Tu pourras aussi envoyer un fichier sur la fiche client." class="min-w-0 sm:col-span-2">
                  <UInput v-model="newClient.logo_url" class="w-full" placeholder="https://…" />
                </UFormField>
                <UFormField label="Photo 1 (URL)" class="min-w-0">
                  <UInput v-model="newClient.photo1_url" class="w-full" placeholder="Portrait / photo principale" />
                </UFormField>
                <UFormField label="Photo 2 (URL)" class="min-w-0">
                  <UInput v-model="newClient.photo2_url" class="w-full" placeholder="Logo alternatif, etc." />
                </UFormField>
                <UFormField label="Notes" class="min-w-0 sm:col-span-2">
                  <textarea
                    v-model="newClient.notes"
                    rows="3"
                    class="focus:ring-primary block w-full resize-y rounded-md border-0 bg-elevated px-3 py-2 text-sm ring ring-default focus:outline-none focus:ring-2"
                    placeholder="Infos internes…"
                  />
                </UFormField>
              </div>
            </div>
          </template>

          <template #footer>
            <div class="flex w-full justify-end gap-2">
              <UButton color="neutral" variant="ghost" @click="createOpen = false">Annuler</UButton>
              <UButton color="primary" :loading="creating" :disabled="!newClient.name" @click="createClient">
                Créer
              </UButton>
            </div>
          </template>
        </UModal>

        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <UCard v-for="c in clients" :key="c.id">
            <template #header>
              <div class="flex items-center gap-3">
                <img v-if="c.logo_url" :src="c.logo_url" class="size-10 rounded bg-white object-contain" />
                <div class="min-w-0">
                  <div class="truncate font-semibold">{{ c.name }}</div>
                  <div v-if="c.firstname || c.lastname" class="text-muted truncate text-xs">
                    {{ [c.firstname, c.lastname].filter(Boolean).join(' ') }}
                  </div>
                  <div v-if="c.subtitle" class="text-muted truncate text-sm">{{ c.subtitle }}</div>
                </div>
              </div>
            </template>

            <div class="space-y-2 text-sm">
              <div v-if="c.website_url" class="truncate">{{ c.website_url }}</div>
              <div v-if="c.email" class="truncate">{{ c.email }}</div>
              <div v-if="c.phone_primary" class="truncate">{{ c.phone_primary }}</div>
            </div>

            <template #footer>
              <div class="flex justify-end">
                <UButton :to="`/clients/${c.id}`" color="primary" variant="soft">Ouvrir</UButton>
              </div>
            </template>
          </UCard>
        </div>
      </div>
    </template>
  </UDashboardPanel>
</template>

