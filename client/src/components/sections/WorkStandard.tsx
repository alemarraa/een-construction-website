import { IMAGES } from "@/data/images"

const STANDARDS = [
  "Dust control and surface protection on every job",
  "Texture and finish matched to existing unit surfaces",
  "All trades sequenced to avoid re-work",
  "Punch list reviewed with you before close-out",
  "Debris removed and site cleaned before final walkthrough",
  "Direct communication throughout — no chasing updates",
]

export default function WorkStandard() {
  return (
    <section className="bg-stone-100 py-24 text-[#11100d] lg:py-32" aria-labelledby="standard-heading">
      <div className="container">
        <div className="grid gap-16 lg:grid-cols-2 lg:gap-0 lg:items-stretch">
          {/* ── LEFT: Image ── */}
          <div className="relative lg:pr-16">
            <div className="relative h-full min-h-[400px]">
              {/* Offset shadow */}
              <div className="absolute -bottom-4 -left-4 h-full w-full border-2 border-[#11100d]" aria-hidden="true" />
              <img
                src={IMAGES.worker}
                alt="EEN Construction tile installation detail — clean finish work"
                className="relative z-10 h-full w-full object-cover shadow-[16px_16px_0_rgba(0,0,0,0.18)]"
                loading="lazy"
              />
            </div>

            {/* Label chip */}
            <div className="absolute bottom-8 right-4 z-20 border-2 border-[#11100d] bg-yellow-400 px-4 py-2 shadow-[4px_4px_0_rgba(0,0,0,0.2)] lg:bottom-8 lg:right-8">
              <span className="text-[0.6rem] font-black uppercase tracking-[0.2em] text-black">Tile &amp; Finish Work</span>
            </div>
          </div>

          {/* ── RIGHT: Copy + Standards ── */}
          <div className="flex flex-col justify-center lg:pl-16">
            <p className="mb-4 text-xs font-black uppercase tracking-[0.22em] text-yellow-600">
              Work Standard
            </p>
            <h2
              id="standard-heading"
              className="mb-6 font-display text-4xl font-black uppercase leading-[0.92] tracking-tight text-[#11100d] sm:text-5xl"
            >
              Tough Work
              <br />
              <span className="text-yellow-600">With a Clean</span>
              <br />
              Finish.
            </h2>
            <p className="mb-8 text-base font-semibold leading-8 text-stone-600">
              Turnaround work happens between tenants. We treat it like it matters&thinsp;&mdash;&thinsp;because rough finishes, missed punch list items, and a dirty unit on lease-up day cost you time and money.
            </p>

            <ul className="flex flex-col border-l-4 border-[#11100d] pl-6" role="list">
              {STANDARDS.map((standard) => (
                <li key={standard} className="flex items-start gap-3 py-3 border-b border-stone-300 last:border-0">
                  <span
                    className="mt-2 h-2 w-2 flex-shrink-0 bg-yellow-500"
                    aria-hidden="true"
                  />
                  <span className="text-sm font-semibold leading-7 text-stone-700">{standard}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  )
}
