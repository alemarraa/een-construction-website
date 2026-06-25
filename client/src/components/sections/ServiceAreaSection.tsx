import { SERVICE_COUNTIES, SERVICE_AREA_NOTE } from "@/data/serviceArea"
import { MapPin, ArrowRight } from "lucide-react"

export default function ServiceAreaSection() {
  return (
    <section
      id="service-area"
      className="scroll-mt-20 bg-[#0d0d0b] py-24 lg:py-32"
      aria-labelledby="service-area-heading"
    >
      <div className="container">
        <div className="grid gap-16 lg:grid-cols-2 lg:gap-24 lg:items-start">
          {/* ── LEFT: Heading + note ── */}
          <div>
            <p className="mb-4 text-xs font-black uppercase tracking-[0.22em] text-yellow-400">
              Where We Work
            </p>
            <h2
              id="service-area-heading"
              className="mb-8 font-display text-4xl font-black uppercase leading-[0.92] tracking-tight text-white sm:text-5xl lg:text-6xl"
            >
              Maryland
              <br />
              <span className="text-yellow-400">Multifamily</span>
              <br />
              Coverage.
            </h2>
            <p className="mb-8 max-w-sm text-base font-semibold leading-8 text-stone-400">
              Currently serving Montgomery County and Prince George's County. More counties coming as we grow.
            </p>

            {/* CTA card */}
            <div className="border border-yellow-400/30 bg-yellow-400/5 p-6">
              <div className="mb-3 flex h-10 w-10 items-center justify-center border border-yellow-400/40 bg-yellow-400/10">
                <MapPin className="h-5 w-5 text-yellow-400" aria-hidden="true" />
              </div>
              <h3 className="mb-2 font-display text-lg font-black uppercase text-white">
                Not on the list?
              </h3>
              <p className="mb-5 text-sm font-semibold leading-6 text-stone-400">{SERVICE_AREA_NOTE}</p>
              <a
                href="#contact"
                className="group inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.16em] text-yellow-400 hover:text-yellow-300 transition-colors"
              >
                Contact to Confirm
                <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-1" aria-hidden="true" />
              </a>
            </div>
          </div>

          {/* ── RIGHT: Counties ── */}
          <div>
            {/* Maryland label */}
            <div className="mb-6 flex items-center gap-4">
              <div className="h-px flex-1 bg-white/10" aria-hidden="true" />
              <span className="text-[0.6rem] font-black uppercase tracking-[0.22em] text-stone-600">
                Active Service Counties
              </span>
              <div className="h-px flex-1 bg-white/10" aria-hidden="true" />
            </div>

            <ul
              className="grid grid-cols-1 gap-px bg-white/8 sm:grid-cols-2"
              role="list"
              aria-label="Served Maryland counties"
            >
              {SERVICE_COUNTIES.map((county, i) => (
                <li
                  key={county.name}
                  className={`group flex items-center gap-4 p-5 transition-colors duration-200 ${
                    county.active
                      ? "bg-[#111110] hover:bg-white/[0.05]"
                      : "bg-[#111110] opacity-40"
                  }`}
                >
                  {/* Index number */}
                  <span className="font-display text-2xl font-black leading-none text-yellow-400/30 group-hover:text-yellow-400/60 transition-colors duration-200">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span>
                    <span className="block text-sm font-black uppercase tracking-[0.1em] text-white">
                      {county.name}
                    </span>
                    {county.active && (
                      <span className="mt-0.5 flex items-center gap-1.5">
                        <MapPin className="h-3 w-3 text-yellow-400" aria-hidden="true" />
                        <span className="text-[0.6rem] font-black uppercase tracking-[0.14em] text-yellow-400">Active</span>
                      </span>
                    )}
                  </span>
                  {!county.active && <span className="sr-only">(coming soon)</span>}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  )
}
