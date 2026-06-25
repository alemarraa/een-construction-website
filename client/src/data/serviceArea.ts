export interface ServiceCounty {
  name: string
  active: boolean
  cities: string[]
}

export const SERVICE_COUNTIES: ServiceCounty[] = [
  {
    name: "Montgomery County",
    active: true,
    cities: ["Silver Spring", "Rockville", "Bethesda", "Gaithersburg", "Germantown", "Wheaton", "Takoma Park", "Aspen Hill"],
  },
  {
    name: "Prince George's County",
    active: true,
    cities: ["Hyattsville", "College Park", "Laurel", "Greenbelt", "Bowie", "Langley Park", "Capitol Heights", "Landover"],
  },
]

export const SERVICE_AREA_NOTE =
  "EEN Construction currently serves multifamily rental properties of four or more units in Montgomery and Prince George's County. Reach out to discuss your property."
