import { BUSINESS } from "@/config"
import { Phone, Mail, ArrowUpRight } from "lucide-react"

const logoUrl = `${import.meta.env.BASE_URL}een-logo.png`

const FOOTER_SERVICES = [
  "Full Unit Turnarounds",
  "Interior Painting",
  "Drywall Repair",
  "Tile Repair",
  "Demolition & Clean-Outs",
  "Fixture Repairs & Punch Lists",
]

const NAV_LINKS = [
  { label: "Services", href: "#services" },
  { label: "Process", href: "#process" },
  { label: "Why EEN", href: "#why-een" },
  { label: "Service Area", href: "#service-area" },
  { label: "FAQ", href: "#faq" },
  { label: "Contact", href: "#contact" },
]

export default function Footer() {
  return (
    <footer className="border-t-4 border-yellow-400 bg-[#0a0a08]" aria-label="Footer">
      <div className="container py-16">
        <div className="grid gap-12 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="sm:col-span-2 lg:col-span-1">
            <a href="#top" className="group mb-6 flex items-center gap-3" aria-label="EEN Construction — back to top">
              <span className="grid h-14 w-14 place-items-center overflow-hidden bg-white p-1.5 shadow-[5px_5px_0_#e5aa00] transition-all duration-200 group-hover:shadow-[7px_7px_0_#e5aa00]">
                <img src={logoUrl} alt="" aria-hidden="true" className="h-full w-full object-contain" />
              </span>
              <span>
                <span className="block font-display text-2xl font-black uppercase leading-none tracking-tight text-white">EEN</span>
                <span className="block text-[0.6rem] font-black uppercase tracking-[0.28em] text-yellow-400 mt-0.5">Construction</span>
              </span>
            </a>
            <p className="max-w-xs text-sm font-semibold leading-relaxed text-stone-500">
              Multifamily unit turnarounds for property managers and landlords with 4+ unit buildings across Maryland.
            </p>

            {/* CTA button */}
            <a href="#contact" className="mt-6 inline-flex items-center gap-2 border border-yellow-400/40 px-5 py-2.5 text-xs font-black uppercase tracking-[0.16em] text-yellow-400 hover:bg-yellow-400 hover:text-black transition-colors duration-200">
              Request Walkthrough
              <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
            </a>
          </div>

          {/* Navigation */}
          <div>
            <h3 className="mb-5 text-[0.6rem] font-black uppercase tracking-[0.22em] text-yellow-400">Navigate</h3>
            <ul className="flex flex-col gap-3" role="list">
              {NAV_LINKS.map((link) => (
                <li key={link.href}>
                  <a href={link.href} className="text-sm font-semibold text-stone-500 hover:text-white transition-colors duration-150">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Services */}
          <div>
            <h3 className="mb-5 text-[0.6rem] font-black uppercase tracking-[0.22em] text-yellow-400">Services</h3>
            <ul className="flex flex-col gap-3" role="list">
              {FOOTER_SERVICES.map((svc) => (
                <li key={svc}>
                  <a href="#services" className="text-sm font-semibold text-stone-500 hover:text-white transition-colors duration-150">
                    {svc}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="mb-5 text-[0.6rem] font-black uppercase tracking-[0.22em] text-yellow-400">Contact</h3>
            <ul className="flex flex-col gap-5" role="list">
              <li>
                <a
                  href={BUSINESS.phoneTel}
                  className="group flex items-start gap-3 text-sm font-semibold text-stone-500 hover:text-white transition-colors duration-150"
                  aria-label={`Call ${BUSINESS.phone}`}
                >
                  <Phone className="mt-0.5 h-4 w-4 flex-shrink-0 text-yellow-400 group-hover:text-yellow-300" aria-hidden="true" />
                  {BUSINESS.phone}
                </a>
              </li>
              <li>
                <a
                  href={BUSINESS.gmailComposeUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group flex items-start gap-3 text-sm font-semibold text-stone-500 hover:text-white transition-colors duration-150"
                  aria-label={`Email ${BUSINESS.email}`}
                >
                  <Mail className="mt-0.5 h-4 w-4 flex-shrink-0 text-yellow-400 group-hover:text-yellow-300" aria-hidden="true" />
                  <span className="break-all">{BUSINESS.email}</span>
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-12 flex flex-col items-start justify-between gap-4 border-t border-white/8 pt-8 sm:flex-row sm:items-center">
          <p className="text-[0.65rem] font-black uppercase tracking-[0.18em] text-stone-600">
            Maryland &bull; Multifamily Turnarounds &bull; 4+ Units
          </p>
          <p className="text-[0.65rem] font-semibold text-stone-600">
            &copy; {new Date().getFullYear()} {BUSINESS.name}. All Rights Reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}
