import { Building2, PaintBucket, Layers, Grid2x2, Hammer, Wrench } from "lucide-react"
import type { LucideIcon } from "lucide-react"

export interface Service {
  id: string
  title: string
  description: string
  icon: LucideIcon
}

export const SERVICES: Service[] = [
  {
    id: "turnarounds",
    title: "Full Unit Turnarounds",
    description: "One crew manages the complete scope so you make one call instead of coordinating four separate contractors. Paint, drywall, tile, demo, fixtures, and punch list — all handled.",
    icon: Building2,
  },
  {
    id: "painting",
    title: "Interior Painting",
    description: "Full unit repaints between tenants. Surface prep, tight cut lines, and durable finish coats built to hold through the next lease cycle.",
    icon: PaintBucket,
  },
  {
    id: "drywall",
    title: "Drywall Repair & Finishing",
    description: "Patch holes, dings, and damage from outgoing tenants. Tape, mud, sand, and texture-match until walls look move-in ready.",
    icon: Layers,
  },
  {
    id: "tile",
    title: "Tile Repair & Replacement",
    description: "Bathroom tile, kitchen backsplashes, floor tile, and grout refreshes. Cracked or stained tile replaced before the next tenant signs.",
    icon: Grid2x2,
  },
  {
    id: "demo",
    title: "Demolition & Clean-Outs",
    description: "Selective demo, old fixture removal, and full debris control. Site is clean and staged so the next phase starts immediately.",
    icon: Hammer,
  },
  {
    id: "punchlist",
    title: "Fixture Repairs & Punch Lists",
    description: "Door hardware, cabinet repairs, caulking, touch-ups, and every line item a property manager needs closed before lease signing.",
    icon: Wrench,
  },
]
