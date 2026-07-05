import type { ComputedRef } from 'vue'
import type { LoginResponse, UserProfile } from '~/types/auth'

/** Auth du portail : login, activation d'invitation, profil courant (rôle → routage). */
export function useAuth() {
  const token = useCookie<string | null>('signdex_token', {
    maxAge: 60 * 60 * 24 * 7, // 7 jours (aligné sur JWT_EXPIRE_HOURS)
    sameSite: 'lax',
    path: '/',
  })
  const user = useState<UserProfile | null>('signdex_user', () => null)

  const isAuthenticated: ComputedRef<boolean> = computed(() => Boolean(token.value))
  const isAdmin: ComputedRef<boolean> = computed(() => user.value?.role === 'admin')
  const isClient: ComputedRef<boolean> = computed(
    () => user.value?.role === 'owner' || user.value?.role === 'editor',
  )

  async function login(email: string, password: string): Promise<UserProfile> {
    const res = await apiFetch<LoginResponse>('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    token.value = res.access_token
    user.value = res.user
    return res.user
  }

  async function acceptInvite(inviteToken: string, password: string): Promise<UserProfile> {
    const res = await apiFetch<LoginResponse>('/auth/accept-invite', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: inviteToken, password }),
    })
    token.value = res.access_token
    user.value = res.user
    return res.user
  }

  async function forgotPassword(email: string): Promise<void> {
    await apiFetch('/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })
  }

  async function resetPassword(resetToken: string, password: string): Promise<UserProfile> {
    const res = await apiFetch<LoginResponse>('/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: resetToken, password }),
    })
    token.value = res.access_token
    user.value = res.user
    return res.user
  }

  async function fetchMe(): Promise<UserProfile | null> {
    if (!token.value) {
      user.value = null
      return null
    }
    try {
      user.value = await apiFetch<UserProfile>('/auth/me')
    } catch {
      user.value = null
      token.value = null
    }
    return user.value
  }

  async function logout(): Promise<void> {
    token.value = null
    user.value = null
    await navigateTo('/login')
  }

  return { token, user, isAuthenticated, isAdmin, isClient, login, acceptInvite, forgotPassword, resetPassword, fetchMe, logout }
}
