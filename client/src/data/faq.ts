export interface FAQItem {
  id: string
  question: string
  answer: string
}

export const FAQ_ITEMS: FAQItem[] = [
  {
    id: "property-types",
    question: "What types of properties do you work with?",
    answer:
      "EEN Construction works with multifamily rental properties that have four or more units in Maryland. This includes apartment buildings, small multifamily complexes, and portfolios managed by property management companies or individual landlords.",
  },
  {
    id: "single-family",
    question: "Do you handle single-family homes or small duplexes?",
    answer:
      "No. EEN Construction focuses exclusively on multifamily properties with four or more units. This specialization allows us to work efficiently within the workflow and timelines that property managers and landlords depend on.",
  },
  {
    id: "turnaround-scope",
    question: "What is included in a unit turnaround?",
    answer:
      "A turnaround covers everything needed to get a vacant unit rent-ready. Depending on the unit's condition, that typically includes interior painting, drywall patching and finishing, tile repair or replacement, fixture repairs, caulking and touch-ups, unit clean-out, and final punch-list closeout. We walk the unit first and scope exactly what is needed.",
  },
  {
    id: "multiple-trades",
    question: "Can you coordinate multiple trades on one unit?",
    answer:
      "Yes. That is the core of what we do. Instead of scheduling a painter, a drywall contractor, and a tile installer separately, EEN Construction manages the full scope with one crew and one point of contact. Work is sequenced and coordinated so the unit moves toward completion without scheduling gaps.",
  },
  {
    id: "multiple-units",
    question: "Can you work on several vacant units at the same time?",
    answer:
      "Yes. We regularly handle multiple vacant units within the same building or portfolio. We discuss the unit count, priority, and schedule during the initial walkthrough and build a plan that keeps multiple turns moving efficiently.",
  },
  {
    id: "service-area",
    question: "What areas of Maryland do you serve?",
    answer:
      "EEN Construction serves multifamily properties across Maryland. Current service counties include Montgomery, Prince George's, Baltimore City, Baltimore County, Anne Arundel, Howard, and Frederick. Contact us to confirm coverage for your specific location.",
  },
  {
    id: "how-to-request",
    question: "How do I request a walkthrough?",
    answer:
      "Use the request form at the bottom of this page, call us directly at (202) 999-6426, or send project details by email. We will confirm and schedule the walkthrough within one business day.",
  },
  {
    id: "after-submit",
    question: "What happens after I submit a request?",
    answer:
      "We review your submission and follow up using your preferred contact method within one business day. If you include a property address and unit count, we can often give you a preliminary scope estimate before the walkthrough.",
  },
  {
    id: "communication",
    question: "Do you provide updates during the job?",
    answer:
      "Yes. We maintain direct communication throughout the project. Before work begins, you receive a clear scope. During the job, we flag anything unexpected immediately. At the end, we do a final walkthrough together to confirm the punch list is closed before we leave.",
  },
]
