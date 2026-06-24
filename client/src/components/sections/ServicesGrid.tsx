import { SERVICES } from "@/data/services"
import { IMAGES } from "@/data/images"

export default function ServicesGrid() {
  return (
    <section
      id="services"
      className="scroll-mt-20 relative overflow-hidden bg-[#111110] py-24 lg:py-32"
      aria-labelledby="services-heading"
    >
      {/* Blueprint bg texture */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.045]"
        style={{ backgroundImage: `url(${IMAGES.blueprint})`, backgroundSize: "cover", backgroundPosition: "center" }}
        aria-hidden="true"
      />

      <div className="container relative z-10">
        {/* Section header */}
        <div className="mb-14 flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="mb-4 text-xs font-black uppercase tracking-[0.22em] text-yellow-400">What We Do</p>
            <h2
              id="services-heading"
              className="font-display text-4xl font-black uppercase leading-[0.92] tracking-tight text-white sm:text-5xl lg:text-6xl"
            >
              One Crew.
              <br />
              <span className="text-yellow-400">Unit Ready.</span>
            </h2>
          </div>
          <p className="max-w-xs text-sm font-semibold leading-7 text-stone-400 lg:text-right">
            Every trade needed between tenants — managed by a single crew with a single point of contact.
          </p>
        </div>

        {/* Service cards grid */}
        <div className="grid gap-px bg-white/10 sm:grid-cols-2 lg:grid-cols-3" role="list">
          {SERVICES.map((service, i) => {
            const Icon = service.icon
            return (
              <article
                key={service.id}
                role="listitem"
                className="group relative overflow-hidden bg-[#111110] p-8 transition-colors duration-300 hover:bg-[#1a1a18]"
              >
                {/* Number watermark */}
                <span
                  className="pointer-events-none absolute right-5 top-4 select-none font-display text-7xl font-black leading-none text-white/[0.04] transition-all duration-300 group-hover:text-yellow-400/[0.08]"
                  aria-hidden="true"
                >
                  {String(i + 1).padStart(2, "0")}
                </span>

                {/* Yellow left border hover indicator */}
                <div className="absolute bottom-0 left-0 top-0 w-0.5 bg-yellow-400 opacity-0 transition-opacity duration-300 group-hover:opacity-100" aria-hidden="true" />

                {/* Icon */}
                <div className="mb-5 flex h-14 w-14 items-center justify-center border border-yellow-400/25 bg-yellow-400/8 text-yellow-400 transition-all duration-300 group-hover:border-yellow-400 group-hover:bg-yellow-400 group-hover:text-black">
                  <Icon className="h-6 w-6" aria-hidden="true" />
                </div>

                <h3 className="mb-3 font-display text-xl font-black uppercase tracking-tight text-white">
                  {service.title}
                </h3>
                <p className="text-sm font-semibold leading-7 text-stone-400 group-hover:text-stone-300 transition-colors duration-300">
                  {service.description}
                </p>
              </article>
            )
          })}
        </div>

        {/* 4+ unit callout */}
        <div className="mt-px border-l-4 border-yellow-400 bg-yellow-400/5 p-6 sm:p-8">
          <p className="text-sm font-semibold leading-7 text-stone-300">
            <span className="font-black text-yellow-400">4+ unit buildings only.</span>&ensp;EEN Construction works
            exclusively with multifamily rental properties. This focus lets us operate efficiently within property
            management workflows and deliver consistent results across multiple units.
          </p>
        </div>
      </div>
    </section>
  )
}
