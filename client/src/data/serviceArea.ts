export interface ServiceCounty {
  name: string
  active: boolean
}

// Update when coverage is confirmed for each county
export const SERVICE_COUNTIES: ServiceCounty[] = [
  { name: "Montgomery County", active: true },
  { name: "Prince George's County", active: true },
  { name: "Baltimore City", active: true },
  { name: "Baltimore County", active: true },
  { name: "Anne Arundel County", active: true },
  { name: "Howard County", active: true },
  { name: "Frederick County", active: true },
  // TODO: Confirm and add additional counties as service area expands
]

export const SERVICE_AREA_NOTE =
  "EEN Construction works exclusively with multifamily rental properties of four or more units. Contact us to confirm coverage for your specific location."
