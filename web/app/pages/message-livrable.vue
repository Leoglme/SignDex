<script setup lang="ts">
import { DELIVERABLE_COVER_LETTER_DEFAULT, DELIVERABLE_COVER_LETTER_REFERRAL } from '~/constants/deliverableCoverLetterDefault'

const STORAGE_KEY = 'signdex-deliverable-cover-letter'

const message = ref(DELIVERABLE_COVER_LETTER_DEFAULT)
const toast = useToast()
const copying = ref(false)
const preset = ref<'standard' | 'referral'>('standard')

onMounted(() => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved !== null) message.value = saved
  } catch {
    /* navigateur privé / désactivé */
  }
})

watch(
  message,
  (v) => {
    try {
      localStorage.setItem(STORAGE_KEY, v)
    } catch {
      /* ignore */
    }
  },
  { flush: 'post' },
)

async function copyMessage() {
  copying.value = true
  try {
    await navigator.clipboard.writeText(message.value)
    toast.add({ title: 'Message copié dans le presse-papiers', color: 'success' })
  } catch {
    toast.add({
      title: 'Copie impossible',
      description: 'Autorise l’accès au presse-papiers ou sélectionne le texte manuellement.',
      color: 'error',
    })
  } finally {
    copying.value = false
  }
}

function resetDefault() {
  preset.value = 'standard'
  message.value = DELIVERABLE_COVER_LETTER_DEFAULT
  toast.add({ title: 'Texte par défaut restauré', color: 'neutral' })
}

function applyPreset(p: 'standard' | 'referral') {
  preset.value = p
  message.value = p === 'referral' ? DELIVERABLE_COVER_LETTER_REFERRAL : DELIVERABLE_COVER_LETTER_DEFAULT
  toast.add({ title: 'Modèle appliqué', color: 'neutral' })
}
</script>

<template>
  <UDashboardPanel id="message-livrable">
    <template #header>
      <UDashboardNavbar title="Message livrable">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <div class="flex flex-wrap items-center gap-2">
            <UButton to="/deliverables" color="neutral" variant="ghost" icon="i-lucide-package" />
            <UButton color="neutral" variant="soft" icon="i-lucide-rotate-ccw" @click="resetDefault">
              Réinitialiser
            </UButton>
            <UButton color="primary" icon="i-lucide-copy" :loading="copying" @click="copyMessage">
              Copier
            </UButton>
          </div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="flex min-h-[calc(100dvh-7rem)] flex-col gap-3 p-4 sm:p-6">
        <p class="text-muted max-w-3xl shrink-0 text-sm leading-relaxed">
          Personnalise le message envoyé avec ton livrable (ComeUp, mail, etc.). Il est enregistré automatiquement dans ce navigateur.
        </p>
        <div class="flex flex-wrap items-center gap-2">
          <UButton
            color="neutral"
            variant="soft"
            :disabled="preset === 'standard'"
            @click="applyPreset('standard')"
          >
            Modèle standard
          </UButton>
          <UButton
            color="neutral"
            variant="soft"
            :disabled="preset === 'referral'"
            @click="applyPreset('referral')"
          >
            Modèle “merci + recommandation”
          </UButton>
        </div>
        <UFormField label="Corps du message" class="flex min-h-0 flex-1 flex-col">
          <textarea
            v-model="message"
            spellcheck="true"
            rows="28"
            class="focus:ring-primary bg-elevated text-default placeholder:text-dimmed box-border min-h-[max(72vh,36rem)] w-full max-w-4xl flex-1 resize-y rounded-lg px-3 py-3 font-sans text-sm leading-relaxed ring ring-default focus:outline-none focus:ring-2"
            aria-label="Message de livrable pour le client"
          />
        </UFormField>
      </div>
    </template>
  </UDashboardPanel>
</template>
