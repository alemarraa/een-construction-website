import { BUSINESS } from "@/config"
import { Phone } from "lucide-react"

export default function MobileActionBar() {
  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-40 flex h-16 items-stretch border-t border-white/10 bg-[#0d0d0b] shadow-[0_-4px_20px_rgba(0,0,0,.4)] lg:hidden"
      aria-label="Quick contact actions"
    >
      <a
        href={BUSINESS.phoneTel}
        className="flex flex-1 items-center justify-center gap-2 border-r border-white/10 text-sm font-black uppercase tracking-[0.14em] text-white hover:bg-white/5 active:bg-white/10 transition-colors"
        aria-label={`Call EEN Construction at ${BUSINESS.phone}`}
      >
        <Phone className="h-5 w-5 text-yellow-400" aria-hidden="true" />
        Call Now
      </a>
      <a
        href="#contact"
        className="flex flex-1 items-center justify-center text-sm font-black uppercase tracking-[0.14em] bg-yellow-400 text-black hover:bg-yellow-300 active:bg-yellow-500 transition-colors"
      >
        Request Walkthrough
      </a>
    </div>
  )
}
