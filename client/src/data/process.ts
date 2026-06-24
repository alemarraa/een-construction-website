export interface ProcessStep {
  number: string
  title: string
  description: string
}

export const PROCESS_STEPS: ProcessStep[] = [
  {
    number: "01",
    title: "Walkthrough",
    description:
      "We inspect the vacant unit, understand what the next tenant move-in requires, and document the full scope — including anything hidden behind walls or under fixtures.",
  },
  {
    number: "02",
    title: "Scope & Quote",
    description:
      "We organize every required trade into one clear project plan and provide a straightforward quote. No surprise add-ons mid-project.",
  },
  {
    number: "03",
    title: "Work & Updates",
    description:
      "We complete the agreed work with site protection, dust control, and direct communication. If anything changes during the job, you hear about it immediately.",
  },
  {
    number: "04",
    title: "Final Walkthrough",
    description:
      "We review every item on the punch list with you, clean the site, and confirm the unit is ready to lease before we close out the job.",
  },
]
