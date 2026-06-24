import { IMAGES } from "@/data/images"
import { CheckCircle2 } from "lucide-react"

const WHO_WE_SERVE = [
  {
    title: "Property Management Companies",
    description:
      "Multi-unit portfolios need fast, reliable turnarounds that fit your maintenance workflow. One contact. Clear scope. No delays.",
  },
  {
    title: "Independent Landlords",
    description:
      "You own the building, you know the units. We handle the full scope between tenants so you can relist faster without chasing multiple contractors.",
  },
  {
    title: "Real Estate Investors",
    description:
      "Value-add units and acquisition rehabs need a crew that moves efficiently. We scope, price, and execute without hand-holding.",
  },
]

const PAIN_POINTS = [
  "Coordinating 3 separate contractors per vacant unit",
  "Units sitting empty while waiting on scheduling gaps",
  "Inconsistent finish quality between trades",
  "Unclear scope leading to mid-job surprises",
  "No single point of contact for the full job",
]

export default function AudienceSection() {
  return (
    <section
      id="why-een"
      className="bg-stone-100 text-[#11100d] py-24 lg:py-32"
      aria-labelledby="audience-heading"
    >
      <div className="container">
        <div className="grid gap-16 lg:grid-cols-2 lg:gap-0">
          {/* ── LEFT: Who we serve ── */}
          <div className="lg:pr-16 xl:pr-24">
            <p className="mb-4 text-xs font-black uppercase tracking-[0.22em] text-yellow-600">
              Who We Work With
            </p>
            <h2
              id="audience-heading"
              className="mb-10 font-display text-4xl font-black uppercase leading-[0.92] tracking-tight text-[#11100d] sm:text-5xl"
            >
              Built for Owners
              <br />
              <span className="text-yellow-600">Who Can&rsquo;t Afford</span>
              <br />
              Vacancy Drag.
            </h2>
            <div className="flex flex-col gap-8">
              {WHO_WE_SERVE.map((group) => (
                <div key={group.title} className="border-l-4 border-[#11100d] pl-5">
                  <h3 className="mb-2 text-sm font-black uppercase tracking-[0.12em] text-[#11100d]">
                    {group.title}
                  </h3>
                  <p className="text-sm font-semibold leading-7 text-stone-600">{group.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* ── RIGHT: Photo + pain-points overlay ── */}
          <div className="relative">
            <div className="relative">
              {/* Offset border */}
              <div className="absolute -bottom-4 -right-4 h-full w-full border-2 border-yellow-400" aria-hidden="true" />
              <img
                src={IMAGES.services}
                alt="EEN Construction multifamily unit turnaround work"
                className="relative z-10 h-[420px] w-full object-cover shadow-[16px_16px_0_rgba(0,0,0,.18)] lg:h-[540px]"
                loading="lazy"
              />
              {/* Dark overlay gradient */}
              <div
                className="absolute inset-x-0 bottom-0 z-20 h-1/2"
                style={{ background: "linear-gradient(to top,rgba(13,13,11,0.88),transparent)" }}
                aria-hidden="true"
              />
            </div>

            {/* Pain points card — overlaid */}
            <div className="relative z-30 -mt-24 ml-6 mr-0 border-l-4 border-yellow-400 bg-[#0d0d0b] p-6 shadow-[8px_8px_0_rgba(229,170,0,0.2)] lg:-mt-36 lg:ml-8">
              <p className="mb-4 text-[0.6rem] font-black uppercase tracking-[0.22em] text-yellow-400">
                Sound Familiar?
              </p>
              <ul className="flex flex-col gap-3" role="list">
                {PAIN_POINTS.map((point) => (
                  <li key={point} className="flex items-start gap-2.5">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-yellow-400" aria-hidden="true" />
                    <span className="text-xs font-semibold leading-5 text-stone-300">{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
