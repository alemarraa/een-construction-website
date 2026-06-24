// =============================================================================
// EEN Construction — Centralized Business Configuration
// Update this file when verified business information becomes available.
// =============================================================================

export const BUSINESS = {
  name: "EEN Construction",
  tagline: "Multifamily Unit Turnarounds",
  description:
    "EEN Construction handles full unit turnarounds for multifamily properties with 4 or more units across Maryland — paint, drywall, tile, demolition, fixture repairs, and complete punch-list closeout.",

  phone: "(202) 999-6426",
  phoneTel: "tel:+12029996426",
  email: "alessandro.marra@empowerestatesnet.com",
  gmailComposeUrl:
    "https://mail.google.com/mail/?view=cm&to=alessandro.marra@empowerestatesnet.com&su=Unit%20Turnaround%20Request%20-%20EEN%20Construction",

  unitMinimum: 4,
  serviceArea: "Maryland",

  // TODO: Add verified values before production launch
  licenseNumber: null as string | null,
  insuranceVerified: false,
  businessHours: null as string | null,   // e.g. "Mon–Fri 7 am – 6 pm"
  legalAddress: null as string | null,    // physical or mailing address

  googleBusinessUrl: null as string | null,
  privacyPolicyUrl: null as string | null,
  termsUrl: null as string | null,

  social: {
    facebook: null as string | null,
    instagram: null as string | null,
    linkedin: null as string | null,
  },

  // Analytics — add IDs when ready (never commit secrets)
  analytics: {
    gaMeasurementId: null as string | null, // VITE_GA_MEASUREMENT_ID
  },
} as const
