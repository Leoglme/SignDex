export interface PortalOffice {
  id: number
  label: string
  template_key: string
  sort_order: number
  address_street: string | null
  address_cp_city: string | null
  phone_display: string | null
  phone_tel: string | null
}

export interface PortalMember {
  id: number
  firstname: string | null
  lastname: string | null
  title: string | null
  sort_order: number
  offices: PortalOffice[]
}

export interface PortalOrganization {
  id: number
  name: string
  brand_logo_url: string | null
  brand_color: string | null
  sig_logo_url: string | null
  sig_chambers_url: string | null
  show_chambers: boolean
  member_count: number
  signature_count: number
}

export interface PortalOverview {
  organization: PortalOrganization
  members: PortalMember[]
  offices: PortalOffice[]
}

export interface PortalDeliverable {
  id: number
  scope: string
  label: string
  signature_count: number
  created_at: string
}
