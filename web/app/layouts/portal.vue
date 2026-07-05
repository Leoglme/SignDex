<template>
  <UDashboardGroup unit="rem" :style="brandVars">
    <UDashboardSidebar
      id="portal"
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
        <PortalBrandHeader :collapsed="collapsed" />
      </template>

      <template #default="{ collapsed }">
        <UNavigationMenu
          :collapsed="collapsed"
          :items="navItems"
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

const { user } = useAuth()
const { brandVars } = useBrand()
const colorMode = useColorMode()
const open: Ref<boolean> = ref(false)

// La couleur de marque doit teinter TOUTE l'app, y compris le contenu « téléporté »
// (drawers/modales rendus dans <body>) : on pose donc --ui-primary sur :root.
const brandCss: ComputedRef<string> = computed(() =>
  user.value?.brand_color ? `:root{--ui-primary:${user.value.brand_color};}` : '',
)
useHead({ style: [{ id: 'portal-brand-vars', innerHTML: brandCss }] })

const navItems: ComputedRef<NavigationMenuItem[]> = computed(() => [
  {
    label: 'Mes signatures',
    icon: 'i-lucide-mail',
    to: '/mon-espace',
    exact: true,
    onSelect: () => {
      open.value = false
    },
  },
  {
    label: 'Configuration',
    icon: 'i-lucide-sliders-horizontal',
    to: '/mon-espace/configuration',
    onSelect: () => {
      open.value = false
    },
  },
  {
    label: 'Aide',
    icon: 'i-lucide-circle-help',
    to: '/mon-espace/aide',
    onSelect: () => {
      open.value = false
    },
  },
])

// Thème par défaut choisi par l'admin : appliqué UNIQUEMENT au premier passage (préférence
// 'system' = l'utilisateur n'a jamais choisi). Dès qu'il bascule clair/sombre lui-même, son
// choix est respecté et persiste au reload — on ne le réécrase plus.
function applyOrgTheme(): void {
  const preferred = user.value?.default_theme
  if ((preferred === 'light' || preferred === 'dark') && colorMode.preference === 'system') {
    colorMode.preference = preferred
  }
}
onMounted(applyOrgTheme)
watch(() => user.value?.default_theme, applyOrgTheme)
</script>
