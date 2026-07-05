<template>
  <UCard :ui="{ root: 'shadow-lg' }">
    <template #header>
      <div class="flex flex-col items-center gap-2 text-center">
        <img
          v-if="info?.brand_logo_url"
          :src="info.brand_logo_url"
          :alt="info?.organization_name || 'Logo'"
          class="h-11 max-w-[200px] object-contain"
        >
        <span
          v-else
          class="bg-elevated ring-default flex size-12 items-center justify-center rounded-xl ring-1"
        >
          <UIcon name="i-lucide-building-2" class="text-muted size-7" />
        </span>
        <div>
          <h1 class="text-highlighted text-lg font-semibold">{{ info?.organization_name || 'Votre espace' }}</h1>
          <p class="text-muted text-sm">Activer votre accès</p>
        </div>
      </div>
    </template>

    <div v-if="loading" class="space-y-3">
      <USkeleton class="h-4 w-2/3" />
      <USkeleton class="h-10 w-full" />
      <USkeleton class="h-10 w-full" />
    </div>

    <UAlert
      v-else-if="!info?.valid"
      color="error"
      variant="soft"
      icon="i-lucide-link-2-off"
      title="Lien invalide ou expiré"
      description="Ce lien d'invitation n'est plus valable. Demandez à votre administrateur de vous en renvoyer un."
    />

    <UForm v-else :state="state" :validate="validate" class="space-y-4" @submit="onSubmit">
      <p class="text-muted text-sm">
        Bienvenue ! Définissez votre mot de passe pour accéder à l'espace
        <span class="text-highlighted font-medium">{{ info?.organization_name }}</span>.
      </p>
      <UFormField label="Email">
        <UInput :model-value="info?.email || ''" disabled trailing-icon="i-lucide-lock" size="lg" class="w-full" />
      </UFormField>
      <UFormField label="Mot de passe" name="password" hint="8 caractères minimum">
        <UInput
          v-model="state.password"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="new-password"
          size="lg"
          class="w-full"
          :ui="{ trailing: 'pe-1' }"
        >
          <template #trailing>
            <UButton
              color="neutral"
              variant="link"
              size="sm"
              :icon="showPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
              :aria-label="showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
              :aria-pressed="showPassword"
              tabindex="-1"
              @click="showPassword = !showPassword"
            />
          </template>
        </UInput>
      </UFormField>
      <UFormField label="Confirmer le mot de passe" name="confirm">
        <UInput
          v-model="state.confirm"
          :type="showConfirm ? 'text' : 'password'"
          autocomplete="new-password"
          size="lg"
          class="w-full"
          :ui="{ trailing: 'pe-1' }"
        >
          <template #trailing>
            <UButton
              color="neutral"
              variant="link"
              size="sm"
              :icon="showConfirm ? 'i-lucide-eye-off' : 'i-lucide-eye'"
              :aria-label="showConfirm ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
              :aria-pressed="showConfirm"
              tabindex="-1"
              @click="showConfirm = !showConfirm"
            />
          </template>
        </UInput>
      </UFormField>
      <UButton
        type="submit"
        :loading="submitting"
        block
        size="lg"
        color="neutral"
        :style="buttonStyle"
        label="Activer mon accès"
      />
    </UForm>
  </UCard>
</template>

<script setup lang="ts">
import type { ComputedRef } from 'vue'
import type { FormError } from '@nuxt/ui'
import type { InviteInfo } from '~/types/auth'

definePageMeta({ layout: 'auth' })

const route = useRoute()
const { acceptInvite } = useAuth()
const toast = useToast()

const inviteToken = String(route.params.token || '')
const info = ref<InviteInfo | null>(null)
const loading = ref(true)
const submitting = ref(false)
const showPassword = ref(false)
const showConfirm = ref(false)
const state = reactive<{ password: string, confirm: string }>({ password: '', confirm: '' })

const pageTitle: ComputedRef<string> = computed(() =>
  info.value?.organization_name ? `Activer mon accès — ${info.value.organization_name}` : 'Activer mon accès',
)
// Teinte les accents (focus des champs, etc.) à la couleur de l'organisation.
const brandCss: ComputedRef<string> = computed(() =>
  info.value?.brand_color ? `:root{--ui-primary:${info.value.brand_color};}` : '',
)
useHead({ title: pageTitle, style: [{ id: 'invite-brand-vars', innerHTML: brandCss }] })

/** Couleur de texte lisible (noir/blanc) selon la luminance de la couleur de marque. */
function textOn(hex: string): string {
  const h = hex.replace('#', '')
  const full = h.length === 3 ? h.split('').map(c => c + c).join('') : h
  const r = Number.parseInt(full.slice(0, 2), 16)
  const g = Number.parseInt(full.slice(2, 4), 16)
  const b = Number.parseInt(full.slice(4, 6), 16)
  if ([r, g, b].some(Number.isNaN)) return '#ffffff'
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.6 ? '#111827' : '#ffffff'
}

const buttonStyle: ComputedRef<Record<string, string>> = computed(() => {
  const c = info.value?.brand_color
  if (!c) return {}
  return { backgroundColor: c, borderColor: c, color: textOn(c) }
})

onMounted(async () => {
  try {
    info.value = await apiFetch<InviteInfo>(`/auth/invite/${inviteToken}`)
  } catch {
    info.value = { valid: false, email: null, organization_name: null, brand_logo_url: null, brand_color: null }
  } finally {
    loading.value = false
  }
})

function validate(s: typeof state): FormError[] {
  const errors: FormError[] = []
  if (s.password.length < 8) errors.push({ name: 'password', message: '8 caractères minimum' })
  if (s.confirm !== s.password) errors.push({ name: 'confirm', message: 'Les mots de passe ne correspondent pas' })
  return errors
}

async function onSubmit(): Promise<void> {
  submitting.value = true
  try {
    const profile = await acceptInvite(inviteToken, state.password)
    toast.add({ title: 'Accès activé', description: 'Bienvenue dans votre espace.', color: 'success', icon: 'i-lucide-check' })
    await navigateTo(profile.role === 'admin' ? '/' : '/mon-espace')
  } catch {
    toast.add({
      title: 'Activation impossible',
      description: 'Le lien est peut-être expiré. Réessayez ou demandez un nouveau lien.',
      color: 'error',
    })
  } finally {
    submitting.value = false
  }
}
</script>
