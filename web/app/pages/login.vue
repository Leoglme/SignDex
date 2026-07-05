<template>
  <UCard :ui="{ root: 'shadow-lg' }">
    <template #header>
      <div class="flex flex-col items-center gap-2 text-center">
        <img
          v-if="brandLogoUrl"
          :src="brandLogoUrl"
          :alt="organizationName || 'Logo'"
          class="h-11 max-w-[200px] object-contain"
        >
        <span
          v-else
          class="bg-elevated ring-default flex size-12 items-center justify-center overflow-hidden rounded-xl ring-1"
        >
          <img src="/signdex_logo.svg" alt="SignDex" class="size-8 object-contain" width="32" height="32">
        </span>
        <div>
          <h1 class="text-highlighted text-lg font-semibold">{{ organizationName || 'SignDex' }}</h1>
          <p class="text-muted text-sm">Connexion à votre espace</p>
        </div>
      </div>
    </template>

    <UForm :state="state" :validate="validate" class="space-y-4" @submit="onSubmit">
      <UFormField label="Email" name="email">
        <UInput
          v-model="state.email"
          type="email"
          autocomplete="email"
          placeholder="vous@exemple.com"
          size="lg"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Mot de passe" name="password">
        <UInput
          v-model="state.password"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="current-password"
          placeholder="••••••••"
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
      <UButton
        type="submit"
        :loading="loading"
        block
        size="lg"
        :color="brandColor ? 'neutral' : 'primary'"
        :style="brandButtonStyle"
        label="Se connecter"
      />
      <div class="text-center">
        <NuxtLink to="/forgot-password" class="text-muted hover:text-default text-sm transition-colors">
          Mot de passe oublié ?
        </NuxtLink>
      </div>
    </UForm>
  </UCard>
</template>

<script setup lang="ts">
import type { ComputedRef } from 'vue'
import type { FormError, FormSubmitEvent } from '@nuxt/ui'

definePageMeta({ layout: 'auth' })

const { login } = useAuth()
const { loadHostBranding, branding, brandColor, brandLogoUrl, organizationName, brandCss, brandButtonStyle } = useHostBranding()
const toast = useToast()
const colorMode = useColorMode()

// Branding déduit du sous-domaine (ex. lexial.dibodev.fr → couleurs LEXIAL). SSR → sans flash.
await loadHostBranding()

const pageTitle: ComputedRef<string> = computed(() =>
  organizationName.value ? `Connexion — ${organizationName.value}` : 'Connexion — SignDex',
)
useHead({ title: pageTitle, style: [{ id: 'host-brand-vars', innerHTML: brandCss }] })

const state = reactive<{ email: string, password: string }>({ email: '', password: '' })
const loading = ref(false)
const showPassword = ref(false)

/**
 * Valide le formulaire de connexion.
 * @param s état courant du formulaire
 * @returns liste des erreurs (vide si tout est valide)
 */
function validate(s: typeof state): FormError[] {
  const errors: FormError[] = []
  if (!s.email) errors.push({ name: 'email', message: 'Email requis' })
  if (!s.password) errors.push({ name: 'password', message: 'Mot de passe requis' })
  return errors
}

/**
 * Soumet la connexion puis redirige selon le rôle (admin → accueil, client → mon espace).
 * @param _event évènement de soumission Nuxt UI
 */
async function onSubmit(_event: FormSubmitEvent<typeof state>): Promise<void> {
  loading.value = true
  try {
    const profile = await login(state.email.trim().toLowerCase(), state.password)
    await navigateTo(profile.role === 'admin' ? '/' : '/mon-espace')
  } catch {
    toast.add({
      title: 'Connexion impossible',
      description: 'Email ou mot de passe incorrect.',
      color: 'error',
      icon: 'i-lucide-triangle-alert',
    })
  } finally {
    loading.value = false
  }
}

/**
 * Applique le thème par défaut de l'organisation (ex. LEXIAL → clair) pour que le login
 * soit cohérent avec le portail. Hôte non-client (SignDex) → aucune contrainte (préférence conservée).
 */
function applyHostTheme(): void {
  const preferred = branding.value?.default_theme
  // Seulement si l'utilisateur n'a jamais choisi (préférence 'system') → on respecte son choix persistant.
  if ((preferred === 'light' || preferred === 'dark') && colorMode.preference === 'system') {
    colorMode.preference = preferred
  }
}

onMounted(applyHostTheme)
</script>
