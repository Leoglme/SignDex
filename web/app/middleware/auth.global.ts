/**
 * Garde d'authentification globale.
 * - Pages publiques : /login et /invitation/*
 * - Sinon : token requis. Le rôle décide de la zone accessible (admin ↔ client).
 */
export default defineNuxtRouteMiddleware(async (to) => {
  const isPublic
    = to.path === '/login'
      || to.path === '/forgot-password'
      || to.path.startsWith('/invitation')
      || to.path.startsWith('/reset')
  const { token, user, fetchMe } = useAuth()

  if (!token.value) {
    return isPublic ? undefined : navigateTo('/login')
  }

  // Token présent mais profil pas encore chargé (SSR / nouvelle nav) → on récupère le rôle.
  if (!user.value) {
    await fetchMe()
  }
  if (!user.value) {
    // fetchMe a purgé un token invalide.
    return isPublic ? undefined : navigateTo('/login')
  }

  // Déjà connecté et sur /login → accueil selon le rôle.
  if (to.path === '/login') {
    return navigateTo(user.value.role === 'admin' ? '/' : '/mon-espace')
  }

  const isClientArea = to.path.startsWith('/mon-espace')
  if (user.value.role === 'admin') {
    // L'admin pilote depuis « Espaces clients », pas d'espace client personnel.
    if (isClientArea) return navigateTo('/espaces-clients')
    return undefined
  }

  // Client (propriétaire / éditeur) : cantonné à son espace.
  if (!isClientArea && !isPublic) {
    return navigateTo('/mon-espace')
  }
  return undefined
})
