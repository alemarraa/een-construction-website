import { BUSINESS } from "@/config"
import { IMAGES } from "@/data/images"
import { ArrowRight, Phone, Building2, Users, Wrench } from "lucide-react"

const INFO_ITEMS = [
  { icon: Building2, text: "4+ Unit Properties" },
  { icon: Users, text: "One Crew, All Trades" },
  { icon: Wrench, text: "Rent-Ready Closeout" },
]

export default function Hero() {
  return (
    <section
      id="top"
      className="relative min-h-[100svh] overflow-hidden bg-[#0d0d0b] pt-20"
      aria-label="EEN Construction — Multifamily Unit Turnarounds"
    >
      {/* Blueprint grid texture — left half only */}
      <div
        className="pointer-events-none absolute inset-y-0 left-0 w-1/2 opacity-[0.04]"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg,#fff 0,#fff 1px,transparent 1px,transparent 48px),repeating-linear-gradient(90deg,#fff 0,#fff 1px,transparent 1px,transparent 48px)",
        }}
        aria-hidden="true"
      />

      {/* Yellow left-edge bar */}
      <div className="absolute bottom-0 left-0 top-20 w-1 bg-yellow-400/60" aria-hidden="true" />

      <div className="container relative z-10 grid min-h-[calc(100svh-5rem)] grid-cols-1 items-center gap-0 lg:grid-cols-2">
        {/* ── LEFT COLUMN ── */}
        <div className="flex flex-col justify-center py-16 pr-0 lg:py-24 lg:pr-12">
          {/* Badge */}
          <div className="mb-7 inline-flex w-fit items-center gap-2.5 border border-yellow-400/40 bg-yellow-400/10 px-4 py-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-yellow-400" aria-hidden="true" />
            <span className="text-[0.65rem] font-black uppercase tracking-[0.22em] text-yellow-400">
              Maryland &bull; Multifamily &bull; 4+ Units
            </span>
          </div>

          {/* Headline */}
          <h1 className="font-display text-[clamp(3rem,7vw,6rem)] font-black uppercase leading-[0.88] tracking-tight text-white">
            Vacant
            <br />
            <span className="text-yellow-400">Units Back</span>
            <br />
            on the
            <br />
            Market
            <br />
            Faster.
          </h1>

          {/* Sub-copy */}
          <p className="mt-7 max-w-[480px] text-base font-semibold leading-8 text-stone-300">
            EEN Construction handles the complete turnaround for multifamily buildings with{" "}
            <strong className="text-white">4 or more units</strong> in Maryland&thinsp;&mdash;&thinsp;painting,
            drywall, tile, fixtures, demo, and punch list under one crew with zero coordination overhead.
          </p>

          {/* CTAs */}
          <div className="mt-9 flex flex-col gap-4 sm:flex-row sm:items-center">
            <a href="#contact" className="group">
              <span className="industrial-button inline-flex items-center gap-2.5 px-8 py-4 text-sm font-black uppercase tracking-[0.14em]">
                Request a Walkthrough
                <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" aria-hidden="true" />
              </span>
            </a>
            <a
              href={BUSINESS.phoneTel}
              className="flex items-center gap-2 text-sm font-black uppercase tracking-[0.14em] text-stone-400 hover:text-yellow-400 transition-colors"
              aria-label={`Call ${BUSINESS.phone}`}
            >
              <Phone className="h-4 w-4" aria-hidden="true" />
              {BUSINESS.phone}
            </a>
          </div>

          {/* Stats row */}
          <div className="mt-12 flex flex-wrap gap-px border-l-2 border-yellow-400 pl-6">
            {[
              { value: "4+", label: "Unit Minimum" },
              { value: "1 Call", label: "All Trades" },
              { value: "Maryland", label: "Service Area" },
            ].map((s) => (
              <div key={s.label} className="mr-8">
                <div className="font-display text-2xl font-black uppercase text-yellow-400">{s.value}</div>
                <div className="text-[0.6rem] font-black uppercase tracking-[0.18em] text-stone-500">{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* ── RIGHT COLUMN — Photo panel ── */}
        <div className="relative hidden lg:flex lg:h-full lg:items-center lg:justify-end">
          {/* Main image */}
          <div className="relative h-[min(82vh,720px)] w-full max-w-[560px]">
            {/* Yellow offset shadow */}
            <div className="absolute -bottom-4 -right-4 h-full w-full border-2 border-yellow-400/50" aria-hidden="true" />
            <img
              src={IMAGES.hero}
              alt="EEN Construction team completing a multifamily unit turnaround in Maryland"
              className="relative z-10 h-full w-full object-cover"
              loading="eager"
              fetchPriority="high"
            />
            {/* Dark gradient overlay — bottom */}
            <div
              className="absolute inset-x-0 bottom-0 z-20 h-1/3"
              style={{ background: "linear-gradient(to top, rgba(13,13,11,0.85), transparent)" }}
              aria-hidden="true"
            />

            {/* Floating info card */}
            <div className="absolute bottom-6 left-6 z-30 border border-yellow-400/30 bg-[#0d0d0b]/90 p-5 backdrop-blur-md shadow-[8px_8px_0_rgba(229,170,0,0.18)]">
              <p className="mb-4 text-[0.55rem] font-black uppercase tracking-[0.22em] text-yellow-400">
                What We Handle
              </p>
              <ul className="flex flex-col gap-3">
                {INFO_ITEMS.map(({ icon: Icon, text }) => (
                  <li key={text} className="flex items-center gap-3">
                    <span className="flex h-7 w-7 items-center justify-center bg-yellow-400">
                      <Icon className="h-3.5 w-3.5 text-black" aria-hidden="true" />
                    </span>
                    <span className="text-xs font-black uppercase tracking-[0.12em] text-white">{text}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile: full-bleed image strip below content */}
      <div className="relative h-56 w-full overflow-hidden lg:hidden">
        <img
          src={IMAGES.hero}
          alt=""
          aria-hidden="true"
          className="h-full w-full object-cover"
          loading="eager"
        />
        <div
          className="absolute inset-0"
          style={{ background: "linear-gradient(to bottom, rgba(13,13,11,0.7) 0%, transparent 60%, rgba(13,13,11,0.5) 100%)" }}
        />
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-6 left-8 hidden flex-col items-center gap-2 opacity-30 lg:flex" aria-hidden="true">
        <div className="h-12 w-px bg-white" />
        <span className="text-[0.55rem] font-black uppercase tracking-[0.22em] text-white">Scroll</span>
      </div>
    </section>
  )
}
