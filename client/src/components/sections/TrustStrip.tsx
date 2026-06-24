import { Building2, Users, MapPin, CheckCircle2, MessageSquare } from "lucide-react"

const ITEMS = [
  { icon: Building2, value: "4+ Units", label: "Property Minimum" },
  { icon: Users, value: "One Crew", label: "All Trades Covered" },
  { icon: MapPin, value: "Maryland", label: "Service Area" },
  { icon: CheckCircle2, value: "Rent-Ready", label: "Every Closeout" },
  { icon: MessageSquare, value: "Direct Line", label: "No Middlemen" },
]

export default function TrustStrip() {
  return (
    <section
      className="border-y-4 border-black bg-yellow-400"
      aria-label="Key highlights"
    >
      <div className="container">
        <div className="flex flex-wrap items-stretch divide-x-2 divide-black/15">
          {ITEMS.map(({ icon: Icon, value, label }) => (
            <div
              key={label}
              className="flex min-w-[160px] flex-1 items-center gap-3 px-6 py-5"
            >
              <span className="flex h-10 w-10 flex-shrink-0 items-center justify-center bg-black/10">
                <Icon className="h-5 w-5 text-black" aria-hidden="true" />
              </span>
              <span>
                <span className="block font-display text-lg font-black uppercase leading-none tracking-tight text-black">
                  {value}
                </span>
                <span className="block text-[0.6rem] font-black uppercase tracking-[0.18em] text-yellow-900/60 mt-0.5">
                  {label}
                </span>
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
