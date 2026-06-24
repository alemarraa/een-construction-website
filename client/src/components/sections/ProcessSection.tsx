import { PROCESS_STEPS } from "@/data/process"

export default function ProcessSection() {
  return (
    <section
      id="process"
      className="scroll-mt-20 bg-yellow-400 py-24 text-black lg:py-32"
      aria-labelledby="process-heading"
    >
      <div className="container">
        {/* Section header */}
        <div className="mb-14">
          <p className="mb-4 text-xs font-black uppercase tracking-[0.22em] text-yellow-900/60">
            How It Works
          </p>
          <h2
            id="process-heading"
            className="font-display text-4xl font-black uppercase leading-[0.92] tracking-tight text-black sm:text-5xl lg:text-6xl"
          >
            Simple Process.
            <br />
            <span className="text-yellow-900">No Surprises.</span>
          </h2>
        </div>

        {/* Step cards */}
        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PROCESS_STEPS.map((step) => (
            <li
              key={step.number}
              className="group relative overflow-hidden border-2 border-black bg-[#0d0d0b] p-8 shadow-[8px_8px_0_rgba(0,0,0,0.25)] transition-transform duration-200 hover:-translate-y-1"
            >
              {/* Large number */}
              <span className="mb-6 block font-display text-6xl font-black leading-none text-yellow-400">
                {step.number}
              </span>
              <h3 className="mb-3 font-display text-xl font-black uppercase tracking-tight text-white">
                {step.title}
              </h3>
              <p className="text-sm font-semibold leading-7 text-stone-400">{step.description}</p>

              {/* Yellow corner accent */}
              <div className="absolute bottom-0 right-0 h-0 w-0 border-b-[32px] border-r-[32px] border-b-yellow-400 border-r-yellow-400 border-t-transparent border-l-transparent transition-all duration-200 group-hover:border-b-[40px] group-hover:border-r-[40px]" aria-hidden="true" />
            </li>
          ))}
        </ol>

        {/* CTA */}
        <div className="mt-12 flex items-center justify-between border-t-2 border-black/20 pt-10">
          <p className="font-display text-xl font-black uppercase text-black/70">
            Every job starts with a free walkthrough.
          </p>
          <a href="#contact">
            <span className="inline-block border-2 border-black bg-black px-8 py-4 text-sm font-black uppercase tracking-[0.14em] text-yellow-400 shadow-[6px_6px_0_rgba(0,0,0,0.2)] transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-[8px_8px_0_rgba(0,0,0,0.25)]">
              Start With a Walkthrough
            </span>
          </a>
        </div>
      </div>
    </section>
  )
}
