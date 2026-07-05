<template>
  <UDropdownMenu
    :items="signDexUserMenuItems"
    :content="{ align: 'center', collisionPadding: 12 }"
    :ui="{ content: collapsed ? 'w-48' : 'w-(--reka-dropdown-menu-trigger-width)', item: 'cursor-pointer' }"
  >
    <UButton
      color="neutral"
      variant="ghost"
      block
      :square="collapsed"
      class="data-[state=open]:bg-elevated"
      :class="[!collapsed && 'py-2']"
      icon="i-lucide-circle-user"
      :label="collapsed ? undefined : displayName"
      :trailing-icon="collapsed ? undefined : 'i-lucide-chevrons-up-down'"
      :aria-label="collapsed ? 'Compte et paramètres' : undefined"
      :ui="{ label: 'truncate' }"
    />
  </UDropdownMenu>
</template>

<script setup lang="ts">
import type { ComputedRef } from 'vue'
import type { DropdownMenuItem } from '@nuxt/ui'

defineProps<{
  collapsed?: boolean
}>()

const colorMode = useColorMode()
const { user, logout } = useAuth()

const displayName: ComputedRef<string> = computed(() => user.value?.full_name || user.value?.email || 'Compte')

const signDexUserMenuItems: ComputedRef<DropdownMenuItem[][]> = computed(() => [
  [
    {
      label: user.value?.email || 'Compte',
      type: 'label',
    },
  ],
  [
    {
      label: 'Apparence',
      icon: 'i-lucide-sun-moon',
      children: [
        {
          label: 'Clair',
          icon: 'i-lucide-sun',
          class: 'cursor-pointer',
          type: 'checkbox',
          checked: colorMode.value === 'light',
          onSelect(e: Event) {
            e.preventDefault()
            colorMode.preference = 'light'
          },
        },
        {
          label: 'Sombre',
          icon: 'i-lucide-moon',
          class: 'cursor-pointer',
          type: 'checkbox',
          checked: colorMode.value === 'dark',
          onSelect(e: Event) {
            e.preventDefault()
            colorMode.preference = 'dark'
          },
        },
        {
          label: 'Système',
          icon: 'i-lucide-monitor',
          class: 'cursor-pointer',
          type: 'checkbox',
          checked: colorMode.preference === 'system',
          onSelect(e: Event) {
            e.preventDefault()
            colorMode.preference = 'system'
          },
        },
      ],
    },
  ],
  [
    {
      label: 'Se déconnecter',
      icon: 'i-lucide-log-out',
      class: 'cursor-pointer',
      onSelect: () => {
        void logout()
      },
    },
  ],
])
</script>

