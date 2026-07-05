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
          <UIcon name="i-lucide-lock-keyhole" class="text-muted size-7" />
        </span>
        <div>
          <h1 class="text-highlighted text-lg font-semibold">Nouveau mot de passe</h1>
          <p class="text-muted text-sm">{{ info?.organization_name || 'Votre espace' }}</p>
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
      description="Ce lien de réinitialisation n'est plus valable. Demandez-en un nouveau."
    />

    <UForm v-else :state="state" :validate="validate" class="space-y-4" @submit="onSubmit">
      <p class="text-muted text-sm">
        Choisissez un nouveau mot de passe pour
        <span class="text-highlighted font-medium">{{ info?.email }}</span>.
      </p>
      <UFormField label="Nouveau mot de passe" name="password" hint="8 caractères minimum">
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
        label="Enregistrer le mot de passe"
      />
    </UForm>

    <template v-if="!loading && !info?.valid" #footer>
      <div class="text-center">
        <NuxtLink to="/forgot-password" class="text-muted hover:text-default text-sm transition-colors">
          Demander un nouveau lien
        </NuxtLink>
      </div>
    </template>
  </UCard>
</template>

<script setup lang="ts">
import type { ComputedRef } from 'vue'
import type { FormError } from '@nuxt/ui'
import type { ResetInfo } from '~/types/auth'

definePageMeta({ layout: 'auth' })

const route = useRoute()
const { resetPassword } = useAuth()
const toast = useToast()

const resetToken = String(route.params.token || '')
const info = ref<ResetInfo | null>(null)
const loading = ref(true)
const submitting = ref(false)
const showPassword = ref(false)
const showConfirm = ref(false)
const state = reactive<{ password: string, confirm: string }>({ password: '', confirm: '' })

const pageTitle: ComputedRef<string> = computed(() =>
  info.value?.organization_name ? `Nouveau mot de passe — ${info.value.organization_name}` : 'Nouveau mot de passe',
)
// Teinte les accents (focus, bouton) à la couleur de l'organisation liée au token.
const brandCss: ComputedRef<string> = computed(() =>
  info.value?.brand_color ? `:root{--ui-primary:${info.value.brand_color};}` : '',
)
useHead({ title: pageTitle, style: [{ id: 'reset-brand-vars', innerHTML: brandCss }] })

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

/**
 * Valide les deux champs mot de passe.
 * @param s état du formulaire
 * @returns liste des erreurs (vide si valide)
 */
function validate(s: typeof state): FormError[] {
  const errors: FormError[] = []
  if (s.password.length < 8) errors.push({ name: 'password', message: '8 caractères minimum' })
  if (s.confirm !== s.password) errors.push({ name: 'confirm', message: 'Les mots de passe ne correspondent pas' })
  return errors
}

/**
 * Applique le nouveau mot de passe puis connecte et redirige vers l'espace.
 */
async function onSubmit(): Promise<void> {
  submitting.value = true
  try {
    const profile = await resetPassword(resetToken, state.password)
    toast.add({ title: 'Mot de passe mis à jour', description: 'Vous êtes connecté.', color: 'success', icon: 'i-lucide-check' })
    await navigateTo(profile.role === 'admin' ? '/' : '/mon-espace')
  } catch {
    toast.add({
      title: 'Réinitialisation impossible',
      description: 'Le lien est peut-être expiré. Demandez-en un nouveau.',
      color: 'error',
    })
  } finally {
    submitting.value = false
  }
}

onMounted(async (): Promise<void> => {
  try {
    info.value = await apiFetch<ResetInfo>(`/auth/reset/${resetToken}`)
  } catch {
    info.value = { valid: false, email: null, organization_name: null, brand_logo_url: null, brand_color: null }
  } finally {
    loading.value = false
  }
})
</script>
