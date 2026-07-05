export type UserRole = 'admin' | 'owner' | 'editor'
export type AccessStatus = 'invited' | 'active'

export interface UserProfile {
  id: number
  email: string
  role: UserRole
  organization_id: number | null
  full_name: string | null
  is_active: boolean
  organization_name?: string | null
  brand_logo_url?: string | null
  brand_color?: string | null
  default_theme?: 'light' | 'dark' | null
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: UserProfile
}

export interface InviteInfo {
  valid: boolean
  email: string | null
  organization_name: string | null
  brand_logo_url: string | null
  brand_color: string | null
}

/** Branding public déduit du sous-domaine (ex. lexial.dibodev.fr → couleurs LEXIAL). */
export interface HostBranding {
  slug: string
  organization_name: string | null
  brand_logo_url: string | null
  brand_color: string | null
  default_theme: 'light' | 'dark' | null
}

export interface ResetInfo {
  valid: boolean
  email: string | null
  organization_name: string | null
  brand_logo_url: string | null
  brand_color: string | null
}

export interface AccessUser {
  id: number
  email: string
  full_name: string | null
  role: UserRole
  status: AccessStatus
}

export interface InviteLink {
  user: AccessUser
  invite_url: string
}
