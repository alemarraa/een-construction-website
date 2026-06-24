import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { BUSINESS } from "@/config"
import { Menu, X, Phone } from "lucide-react"

const logoUrl = `${import.meta.env.BASE_URL}een-logo.png`

const NAV_LINKS = [
  { label: "Services", href: "#services" },
  { label: "Process", href: "#process" },
  { label: "Why EEN", href: "#why-een" },
  { label: "Service Area", href: "#service-area" },
  { label: "FAQ", href: "#faq" },
  { label: "Contact", href: "#contact" },
]

export default function Header() {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : ""
    return () => { document.body.style.overflow = "" }
  }, [menuOpen])

  const closeMenu = () => setMenuOpen(false)

  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[200] focus:bg-yellow-400 focus:px-4 focus:py-2 focus:text-sm focus:font-black focus:text-black focus:uppercase"
      >
        Skip to main content
      </a>

      <header
        className={`fixed left-0 right-0 top-0 z-50 transition-all duration-300 ${
          scrolled
            ? "border-b border-yellow-400/20 bg-[#0d0d0b] shadow-[0_4px_30px_rgba(0,0,0,.6)]"
            : "border-b border-white/5 bg-[#0d0d0b]/85 backdrop-blur-lg"
        }`}
      >
        {/* Top accent line */}
        <div className="h-0.5 w-full bg-yellow-400" aria-hidden="true" />

        <div className="container flex h-[4.5rem] items-center justify-between gap-4">
          {/* Logo */}
          <a
            href="#top"
            className="group flex items-center gap-3 flex-shrink-0"
            aria-label="EEN Construction — home"
          >
            <span className="grid h-11 w-11 place-items-center overflow-hidden bg-white p-1.5 shadow-[4px_4px_0_#e5aa00] transition-all duration-200 group-hover:shadow-[6px_6px_0_#e5aa00]">
              <img src={logoUrl} alt="" aria-hidden="true" className="h-full w-full object-contain" />
            </span>
            <span className="hidden sm:block">
              <span className="block font-display text-xl font-black uppercase leading-none tracking-tight text-white">
                EEN
              </span>
              <span className="block text-[0.58rem] font-black uppercase tracking-[0.28em] text-yellow-400">
                Construction
              </span>
            </span>
          </a>

          {/* Desktop nav */}
          <nav className="hidden items-center gap-5 xl:flex" aria-label="Primary navigation">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="nav-cut text-[0.7rem] font-black uppercase tracking-[0.16em] text-stone-300 hover:text-yellow-400"
              >
                {link.label}
              </a>
            ))}
          </nav>

          {/* Desktop CTAs */}
          <div className="hidden items-center gap-4 lg:flex">
            <a
              href={BUSINESS.phoneTel}
              className="flex items-center gap-1.5 text-sm font-bold text-stone-300 hover:text-yellow-400 transition-colors"
              aria-label={`Call EEN Construction at ${BUSINESS.phone}`}
            >
              <Phone className="h-4 w-4 text-yellow-400" aria-hidden="true" />
              {BUSINESS.phone}
            </a>
            <a href="#contact">
              <span className="industrial-button inline-block px-5 py-2.5 text-[0.7rem] font-black uppercase tracking-[0.14em]">
                Request Walkthrough
              </span>
            </a>
          </div>

          {/* Mobile controls */}
          <div className="flex items-center gap-2 lg:hidden">
            <a
              href={BUSINESS.phoneTel}
              className="flex h-10 w-10 items-center justify-center text-yellow-400 hover:text-yellow-300"
              aria-label={`Call ${BUSINESS.phone}`}
            >
              <Phone className="h-5 w-5" aria-hidden="true" />
            </a>
            <button
              onClick={() => setMenuOpen(true)}
              className="flex h-10 w-10 items-center justify-center text-white hover:text-yellow-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-yellow-400"
              aria-label="Open navigation menu"
              aria-expanded={menuOpen}
              aria-controls="mobile-menu"
            >
              <Menu className="h-6 w-6" aria-hidden="true" />
            </button>
          </div>
        </div>
      </header>

      {/* Mobile overlay */}
      {menuOpen && (
        <div
          className="fixed inset-0 z-[100] bg-black/70 backdrop-blur-sm"
          onClick={closeMenu}
          aria-hidden="true"
        />
      )}

      {/* Mobile drawer */}
      <div
        id="mobile-menu"
        role="dialog"
        aria-label="Navigation menu"
        aria-modal="true"
        className={`fixed right-0 top-0 z-[101] flex h-full w-[min(320px,100vw)] flex-col bg-[#0d0d0b] border-l border-yellow-400/20 shadow-[-20px_0_60px_rgba(0,0,0,.6)] transition-transform duration-300 ease-in-out ${
          menuOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Drawer top bar */}
        <div className="h-0.5 w-full bg-yellow-400" aria-hidden="true" />
        <div className="flex items-center justify-between border-b border-white/8 px-6 py-5">
          <span className="font-display text-lg font-black uppercase text-white tracking-tight">Menu</span>
          <button
            onClick={closeMenu}
            className="flex h-10 w-10 items-center justify-center text-stone-400 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-yellow-400"
            aria-label="Close navigation menu"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-6 py-6" aria-label="Mobile navigation">
          <ul className="flex flex-col" role="list">
            {NAV_LINKS.map((link) => (
              <li key={link.href}>
                <a
                  href={link.href}
                  onClick={closeMenu}
                  className="flex items-center gap-3 py-4 text-sm font-black uppercase tracking-[0.16em] text-stone-300 hover:text-yellow-400 border-b border-white/5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-yellow-400 transition-colors duration-150"
                >
                  <span className="h-px w-4 bg-yellow-400 flex-shrink-0" aria-hidden="true" />
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="border-t border-white/8 px-6 py-6 flex flex-col gap-3">
          <a href={BUSINESS.phoneTel} className="w-full" onClick={closeMenu}>
            <span className="flex h-12 w-full items-center justify-center gap-2 border-2 border-white/20 text-sm font-black uppercase tracking-[0.14em] text-white hover:border-yellow-400 hover:text-yellow-400 transition-colors duration-150">
              <Phone className="h-4 w-4" aria-hidden="true" />
              {BUSINESS.phone}
            </span>
          </a>
          <a href="#contact" className="w-full" onClick={closeMenu}>
            <span className="industrial-button flex h-12 w-full items-center justify-center text-sm font-black uppercase tracking-[0.14em]">
              Request Walkthrough
            </span>
          </a>
        </div>
      </div>
    </>
  )
}
