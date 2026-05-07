const isDesktopBuild = process.env.NUXT_DESKTOP_BUILD === '1'

export default defineNuxtConfig({
  modules: ['@nuxt/ui'],
  ssr: !isDesktopBuild,

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8010',
    },
  },

  compatibilityDate: '2024-07-11',

  nitro: isDesktopBuild
    ? {
        preset: 'static',
      }
    : undefined,
})

