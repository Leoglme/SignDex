<template>
  <UDashboardGroup unit="rem">
    <UDashboardSidebar
      id="default"
      v-model:open="open"
      collapsible
      resizable
      class="bg-elevated/25"
      :ui="{
        header: 'shrink-0',
        body: 'min-h-0',
        footer: 'lg:border-t lg:border-default shrink-0',
      }"
    >
      <template #header="{ collapsed }">
        <SignDexBrandHeader :collapsed="collapsed" />
      </template>

      <template #default="{ collapsed }">
        <UNavigationMenu
          :collapsed="collapsed"
          :items="signDexMainNavItems"
          orientation="vertical"
          tooltip
          popover
          class="px-0.5"
          :ui="{
            root: 'gap-2',
            list: 'flex flex-col gap-y-2.5',
            item: 'shrink-0',
            link: collapsed ? 'justify-center' : '',
          }"
        />
      </template>

      <template #footer="{ collapsed }">
        <SignDexUserMenu :collapsed="collapsed" />
      </template>
    </UDashboardSidebar>

    <slot />
  </UDashboardGroup>
</template>

<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'
import type { ComputedRef, Ref } from 'vue'

const open: Ref<boolean> = ref(false)

/** Flat list — UNavigationMenu wraps a single group internally; avoids `links[0]` / name clashes with Nuxt. */
const signDexMainNavItems: ComputedRef<NavigationMenuItem[]> = computed(() => [
  {
    label: 'Clients',
    icon: 'i-lucide-users',
    to: '/',
    onSelect: () => {
      open.value = false
    },
  },
  {
    label: 'Templates',
    icon: 'i-lucide-layout-template',
    to: '/templates',
    onSelect: () => {
      open.value = false
    },
  },
  {
    label: 'Livrables',
    icon: 'i-lucide-package',
    to: '/deliverables',
    onSelect: () => {
      open.value = false
    },
  },
  {
    label: 'Message livrable',
    icon: 'i-lucide-mail',
    to: '/message-livrable',
    onSelect: () => {
      open.value = false
    },
  },
])
</script>

