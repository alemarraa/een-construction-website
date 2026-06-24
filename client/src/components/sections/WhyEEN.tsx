import { ArrowRight } from "lucide-react"

const BENEFITS = [
  {
    number: "01",
    title: "One Call, All Trades",
    description:
      "Stop managing four separate contractors. EEN handles painting, drywall, tile, fixtures, and demo under one scope, one crew, and one contact.",
  },
  {
    number: "02",
    title: "Built Around Your Timeline",
    description:
      "Vacant units cost money. We schedule around your leasing timeline and move through the work without gap days waiting on sub-coordination.",
  },
  {
    number: "03",
    title: "No Mid-Job Surprises",
    description:
      "We scope the full unit before we quote. If something changes during work, you hear about it immediately rather than discovering it in the final invoice.",
  },
  {
    number: "04",
    title: "Clean Site, Every Job",
    description:
      "Dust control, site protection, and full debris removal are part of the work. Units are left clean enough to show the day we close out.",
  },
]

export default function WhyEEN() {
  return (
    <section className="bg-[#0d0d0b] py-24 lg:py-32" aria-labelledby="why-heading">
      <div className="container">
        {/* Header row */}
        <div className="mb-14 grid gap-8 lg:grid-cols-2 lg:items-end">
          <div>
            <p className="mb-4 text-xs font-black uppercase tracking-[0.22em] text-yellow-400">Why EEN</p>
            <h2
              id="why-heading"
              className="font-display text-4xl font-black uppercase leading-[0.92] tracking-tight text-white sm:text-5xl lg:text-6xl"
            >
              Fewer Calls.
              <br />
              <span className="text-yellow-400">Faster Turns.</span>
            </h2>
          </div>
          <div className="flex items-end">
            <p className="max-w-sm text-sm font-semibold leading-7 text-stone-400">
              The operational edge that keeps property managers from running a contractor coordination business on the side.
            </p>
          </div>
        </div>

        {/* Benefits — 2x2 staggered */}
        <div className="grid gap-px bg-white/8 sm:grid-cols-2" role="list">
          {BENEFITS.map((benefit) => (
            <div
              key={benefit.number}
              role="listitem"
              className="relative overflow-hidden bg-[#0d0d0b] p-8 transition-colors duration-200 hover:bg-white/[0.04]"
            >
              {/* Giant watermark number */}
              <span
                className="pointer-events-none absolute -right-2 -top-4 select-none font-display text-[8rem] font-black leading-none text-white/[0.03]"
                aria-hidden="true"
              >
                {benefit.number}
              </span>

              <span className="mb-5 block font-display text-5xl font-black leading-none text-yellow-400">
                {benefit.number}
              </span>
              <h3 className="mb-3 font-display text-xl font-black uppercase tracking-tight text-white">
                {benefit.title}
              </h3>
              <p className="relative z-10 text-sm font-semibold leading-7 text-stone-400">{benefit.description}</p>
            </div>
          ))}
        </div>

        {/* CTA row */}
        <div className="mt-10 flex items-center justify-between border-t border-white/8 pt-8">
          <p className="text-sm font-semibold text-stone-500">
            Ready to cut the coordination work?
          </p>
          <a
            href="#contact"
            className="group flex items-center gap-2 text-sm font-black uppercase tracking-[0.14em] text-yellow-400 hover:text-yellow-300 transition-colors"
          >
            Request a Walkthrough
            <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" aria-hidden="true" />
          </a>
        </div>
      </div>
    </section>
  )
}
