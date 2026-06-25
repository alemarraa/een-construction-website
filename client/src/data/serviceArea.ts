export interface ServiceCounty {
  name: string
  active: boolean
}

// Update when coverage is confirmed for each county
export const SERVICE_COUNTIES: ServiceCounty[] = [
  { name: "Montgomery County", active: true },
  { name: "Prince George's County", active: true },
]

export const SERVICE_AREA_NOTE =
  "EEN Construction currently serves multifamily rental properties of four or more units in Montgomery and Prince George's County. Reach out to discuss your property."
