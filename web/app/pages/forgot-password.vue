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
          <h1 class="text-highlighted text-lg font-semibold">Mot de passe oublié</h1>
          <p class="text-muted text-sm">{{ organizationName || 'Votre espace' }}</p>
        </div>
      </div>
    </template>

    <UAlert
      v-if="sent"
      color="success"
      variant="soft"
      icon="i-lucide-mail-check"
      title="Email envoyé"
      :description="`Si un compte existe pour ${state.email}, un lien de réinitialisation vient d'être envoyé. Pensez à vérifier vos spams.`"
    />

    <UForm v-else :state="state" :validate="validate" class="space-y-4" @submit="onSubmit">
      <p class="text-muted text-sm">
        Saisissez votre email : nous vous enverrons un lien pour choisir un nouveau mot de passe.
      </p>
      <UFormField label="Email" name="email">
        <UInput
          v-model="state.email"
          type="email"
          autocomplete="email"
          placeholder="vous@exemple.com"
          size="lg"
          class="w-full"
          leading-icon="i-lucide-mail"
        />
      </UFormField>
      <UButton
        type="submit"
        :loading="loading"
        block
        size="lg"
        :color="brandColor ? 'neutral' : 'primary'"
        :style="brandButtonStyle"
        label="Envoyer le lien"
      />
    </UForm>
  </UCard>

  <div class="mt-5 text-center">
    <NuxtLink to="/login" class="text-muted hover:text-default text-sm transition-colors">
      ← Retour à la connexion
    </NuxtLink>
  </div>
</template>

<script setup lang="ts">
import type { ComputedRef } from 'vue'
import type { FormError, FormSubmitEvent } from '@nuxt/ui'

definePageMeta({ layout: 'auth' })

const { forgotPassword } = useAuth()
const { loadHostBranding, branding, brandColor, brandLogoUrl, organizationName, brandCss, brandButtonStyle } = useHostBranding()
const colorMode = useColorMode()

// Branding déduit du sous-domaine (ex. lexial.dibodev.fr → couleurs LEXIAL).
await loadHostBranding()

const pageTitle: ComputedRef<string> = computed(() =>
  organizationName.value ? `Mot de passe oublié — ${organizationName.value}` : 'Mot de passe oublié',
)
useHead({ title: pageTitle, style: [{ id: 'host-brand-vars', innerHTML: brandCss }] })

const state = reactive<{ email: string }>({ email: '' })
const loading = ref(false)
const sent = ref(false)

/**
 * Valide l'email saisi.
 * @param s état du formulaire
 * @returns liste des erreurs (vide si valide)
 */
function validate(s: typeof state): FormError[] {
  const errors: FormError[] = []
  if (!s.email) errors.push({ name: 'email', message: 'Email requis' })
  return errors
}

/**
 * Envoie la demande de réinitialisation. Affiche TOUJOURS l'état « envoyé » (aucune fuite d'info).
 * @param _event évènement de soumission Nuxt UI
 */
async function onSubmit(_event: FormSubmitEvent<typeof state>): Promise<void> {
  loading.value = true
  try {
    await forgotPassword(state.email.trim().toLowerCase())
  } finally {
    loading.value = false
    sent.value = true
  }
}

/** Applique le thème par défaut de l'organisation (cohérence avec le portail). */
function applyHostTheme(): void {
  const preferred = branding.value?.default_theme
  // Seulement si l'utilisateur n'a jamais choisi (préférence 'system') → on respecte son choix persistant.
  if ((preferred === 'light' || preferred === 'dark') && colorMode.preference === 'system') {
    colorMode.preference = preferred
  }
}

onMounted(applyHostTheme)
</script>
