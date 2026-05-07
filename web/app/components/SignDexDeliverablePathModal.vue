<template>
  <UModal
    v-model:open="open"
    title="Livrable enregistré"
    description="Le fichier ZIP a été enregistré sur ton ordinateur. Tu peux copier le chemin ci-dessous."
    class="sm:max-w-2xl"
  >
    <template #body>
      <div class="space-y-3">
        <div
          class="border-default bg-elevated/50 max-h-40 overflow-y-auto rounded-lg border px-3 py-2 font-mono text-xs break-all"
        >
          {{ path || '—' }}
        </div>
        <UButton
          icon="i-lucide-copy"
          color="primary"
          variant="soft"
          :disabled="!path"
          @click="copyPath"
        >
          Copier le chemin
        </UButton>
      </div>
    </template>

    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton color="neutral" variant="ghost" @click="dismiss">Fermer</UButton>
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
const open = defineModel<boolean>('open', { default: false })

const props = defineProps<{
  path: string
}>()

const toast = useToast()

function dismiss() {
  open.value = false
}

async function copyPath() {
  if (!props.path) return
  try {
    await navigator.clipboard.writeText(props.path)
    toast.add({ title: 'Chemin copié', color: 'success' })
  } catch {
    toast.add({
      title: 'Copie impossible',
      description: 'Sélectionne le texte manuellement ou vérifie les permissions du navigateur.',
      color: 'error',
    })
  }
}
</script>
