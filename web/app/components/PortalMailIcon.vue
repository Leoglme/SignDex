<template>
  <!-- Gmail : logo officiel (Iconify « logos », MIT) -->
  <UIcon v-if="client === 'gmail'" name="i-logos-google-gmail" :style="dim" />

  <!-- Outlook : logo (Iconify « vscode-icons », MIT) -->
  <svg v-else-if="client === 'outlook'" :style="dim" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path fill="#0072c6" d="M19.484 7.937v5.477l1.916 1.205a.5.5 0 0 0 .21 0l8.238-5.554a1.174 1.174 0 0 0-.959-1.128Z" />
    <path fill="#0072c6" d="m19.484 15.457l1.747 1.2a.52.52 0 0 0 .543 0c-.3.181 8.073-5.378 8.073-5.378v10.066a1.408 1.408 0 0 1-1.49 1.555h-8.874zm-9.044-2.525a1.61 1.61 0 0 0-1.42.838a4.13 4.13 0 0 0-.526 2.218A4.05 4.05 0 0 0 9.02 18.2a1.6 1.6 0 0 0 2.771.022a4 4 0 0 0 .515-2.2a4.37 4.37 0 0 0-.5-2.281a1.54 1.54 0 0 0-1.366-.809" />
    <path fill="#0072c6" d="M2.153 5.155v21.427L18.453 30V2Zm10.908 14.336a3.23 3.23 0 0 1-2.7 1.361a3.19 3.19 0 0 1-2.64-1.318A5.46 5.46 0 0 1 6.706 16.1a5.87 5.87 0 0 1 1.036-3.616a3.27 3.27 0 0 1 2.744-1.384a3.12 3.12 0 0 1 2.61 1.321a5.64 5.64 0 0 1 1 3.484a5.76 5.76 0 0 1-1.035 3.586" />
  </svg>

  <!-- Apple Mail : tuile enveloppe bleue façon macOS Mail (recréation) -->
  <svg v-else :style="dim" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <defs>
      <linearGradient :id="gradId" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#37c6ff" />
        <stop offset="1" stop-color="#0a7bff" />
      </linearGradient>
    </defs>
    <rect x="1.5" y="1.5" width="29" height="29" rx="7" :fill="`url(#${gradId})`" />
    <rect x="6.5" y="10.5" width="19" height="12" rx="2.5" fill="none" stroke="#ffffff" stroke-width="2" />
    <path d="M7.5 12 16 18.5 24.5 12" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
  </svg>
</template>

<script setup lang="ts">
import type { ComputedRef } from 'vue'
import { useId } from 'vue'

const props = defineProps<{
  client: 'outlook' | 'gmail' | 'apple'
  px?: number
}>()

const dim: ComputedRef<Record<string, string>> = computed(() => {
  const s = `${props.px || 24}px`
  return { width: s, height: s, fontSize: s }
})
const gradId = useId()
</script>
