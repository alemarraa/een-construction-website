import { useState } from "react"
import { FAQ_ITEMS } from "@/data/faq"
import { BUSINESS } from "@/config"
import { ChevronDown, Phone, ArrowRight } from "lucide-react"

export default function FAQSection() {
  const [open, setOpen] = useState<string | null>(null)

  const toggle = (id: string) => setOpen((prev) => (prev === id ? null : id))

  return (
    <section
      id="faq"
      className="scroll-mt-20 bg-[#111110] py-24 lg:py-32"
      aria-labelledby="faq-heading"
    >
      <div className="container">
        <div className="grid gap-16 lg:grid-cols-[1fr_1.6fr] lg:gap-24">
          {/* ── LEFT: Heading + contact nudge ── */}
          <div className="lg:sticky lg:top-24 lg:self-start">
            <p className="mb-4 text-xs font-black uppercase tracking-[0.22em] text-yellow-400">Questions</p>
            <h2
              id="faq-heading"
              className="mb-6 font-display text-4xl font-black uppercase leading-[0.92] tracking-tight text-white sm:text-5xl"
            >
              Common
              <br />
              <span className="text-yellow-400">Questions</span>
            </h2>
            <p className="mb-10 max-w-xs text-sm font-semibold leading-7 text-stone-400">
              If you don't see your question here, call us directly or submit a walkthrough request and we'll reply within one business day.
            </p>

            {/* Contact nudge */}
            <div className="flex flex-col gap-4">
              <a
                href={BUSINESS.phoneTel}
                className="group flex items-center gap-3 border border-white/10 bg-white/[0.03] p-4 hover:border-yellow-400/40 hover:bg-yellow-400/5 transition-all duration-200"
                aria-label={`Call ${BUSINESS.phone}`}
              >
                <span className="flex h-10 w-10 flex-shrink-0 items-center justify-center bg-yellow-400">
                  <Phone className="h-4 w-4 text-black" aria-hidden="true" />
                </span>
                <span>
                  <span className="block text-[0.6rem] font-black uppercase tracking-[0.18em] text-stone-500">Call Direct</span>
                  <span className="block text-sm font-black text-white">{BUSINESS.phone}</span>
                </span>
              </a>

              <a
                href="#contact"
                className="group flex items-center justify-between border border-yellow-400/30 bg-yellow-400/5 p-4 hover:bg-yellow-400/10 transition-colors duration-200"
              >
                <span className="text-sm font-black uppercase tracking-[0.12em] text-yellow-400">Request Walkthrough</span>
                <ArrowRight className="h-4 w-4 text-yellow-400 transition-transform duration-200 group-hover:translate-x-1" aria-hidden="true" />
              </a>
            </div>
          </div>

          {/* ── RIGHT: Accordion ── */}
          <div>
            <dl className="flex flex-col divide-y divide-white/8 border-t border-white/8">
              {FAQ_ITEMS.map((item) => {
                const isOpen = open === item.id
                return (
                  <div key={item.id} className={`transition-colors duration-200 ${isOpen ? "bg-white/[0.03]" : ""}`}>
                    <dt>
                      <button
                        id={`faq-btn-${item.id}`}
                        aria-expanded={isOpen}
                        aria-controls={`faq-panel-${item.id}`}
                        onClick={() => toggle(item.id)}
                        className="flex w-full items-start justify-between gap-6 px-4 py-5 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-yellow-400"
                      >
                        <span className="text-sm font-black uppercase tracking-[0.1em] text-white">
                          {item.question}
                        </span>
                        <ChevronDown
                          className={`mt-0.5 h-5 w-5 flex-shrink-0 text-yellow-400 transition-transform duration-200 ${
                            isOpen ? "rotate-180" : ""
                          }`}
                          aria-hidden="true"
                        />
                      </button>
                    </dt>
                    <dd
                      id={`faq-panel-${item.id}`}
                      role="region"
                      aria-labelledby={`faq-btn-${item.id}`}
                      hidden={!isOpen}
                      className={`overflow-hidden transition-all duration-200 ${isOpen ? "pb-5 px-4" : ""}`}
                    >
                      <p className="text-sm font-semibold leading-7 text-stone-400">{item.answer}</p>
                    </dd>
                  </div>
                )
              })}
            </dl>
          </div>
        </div>
      </div>
    </section>
  )
}
