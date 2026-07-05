<template>
  <div
    class="flex shrink-0 items-center"
    :class="isCollapsed ? 'w-full justify-center px-1 py-2.5' : 'min-w-0 gap-2 px-1 py-2'"
  >
    <!-- Replié : pastille avec l'initiale de l'organisation -->
    <span
      v-if="isCollapsed"
      class="bg-elevated/40 ring-default/40 text-highlighted flex size-9 items-center justify-center rounded-lg text-sm font-semibold ring-1"
    >
      {{ initial }}
    </span>

    <!-- Déplié : logo de l'organisation (ou nom si pas de logo) -->
    <template v-else>
      <img
        v-if="logo"
        :src="logo"
        :alt="orgName"
        class="h-6 max-w-[150px] object-contain"
      >
      <span v-else class="text-highlighted min-w-0 truncate font-semibold">{{ orgName }}</span>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { ComputedRef } from 'vue'

const props = defineProps<{
  collapsed?: boolean
}>()

const { user } = useAuth()

const isCollapsed: ComputedRef<boolean> = computed(() => Boolean(props.collapsed))
const orgName: ComputedRef<string> = computed(() => user.value?.organization_name || 'Mon espace')
const logo: ComputedRef<string | null> = computed(() => user.value?.brand_logo_url || null)
const initial: ComputedRef<string> = computed(() => (orgName.value.trim()[0] || 'M').toUpperCase())
</script>
