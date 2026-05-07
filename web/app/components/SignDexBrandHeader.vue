<template>
  <NuxtLink
    to="/"
    class="hover:bg-elevated/80 flex shrink-0 items-center rounded-lg transition-colors"
    :class="isCollapsed ? 'w-full min-w-9 justify-center px-1 py-2.5' : 'min-w-0 gap-2 px-2 py-2'"
  >
    <span class="bg-elevated/40 ring-default/40 flex size-9 shrink-0 items-center justify-center overflow-hidden rounded-lg ring-1">
      <img src="/signdex_logo.svg" alt="SignDex" class="size-8 max-h-8 max-w-8 object-contain" width="32" height="32" />
    </span>
    <span v-if="!isCollapsed" class="text-highlighted min-w-0 truncate font-semibold">SignDex</span>
  </NuxtLink>
</template>

<script setup lang="ts">
import type { ComputedRef } from 'vue'

const props = defineProps<{
  collapsed?: boolean
}>()

const isCollapsed: ComputedRef<boolean> = computed(() => Boolean(props.collapsed))
</script>

