import { useState } from "react"
import { cn } from "@/lib/utils"

type SiteImageProps = {
  src: string
  alt: string
  className?: string
  /** Small caption shown on the fallback panel when the image can't load. */
  fallbackLabel?: string
  loading?: "lazy" | "eager"
  fetchPriority?: "high" | "low" | "auto"
  decorative?: boolean
}

/**
 * Photo slot that never shows a broken-image icon.
 *
 * If the file is missing or fails to load, it renders a dark blueprint panel in
 * the site's own design language instead, so a bad image path degrades into
 * something intentional rather than a grey box with alt text.
 */
export default function SiteImage({
  src,
  alt,
  className,
  fallbackLabel = "EEN Construction",
  loading = "lazy",
  fetchPriority,
  decorative = false,
}: SiteImageProps) {
  const [failed, setFailed] = useState(false)

  if (failed) {
    return (
      <div
        className={cn("relative overflow-hidden bg-[#0d0d0b]", className)}
        role={decorative ? undefined : "img"}
        aria-label={decorative ? undefined : alt}
        aria-hidden={decorative ? "true" : undefined}
      >
        {/* Blueprint grid */}
        <div
          className="absolute inset-0 opacity-[0.12]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(0deg,#fff 0,#fff 1px,transparent 1px,transparent 40px),repeating-linear-gradient(90deg,#fff 0,#fff 1px,transparent 1px,transparent 40px)",
          }}
          aria-hidden="true"
        />
        {/* Hazard stripe */}
        <div
          className="absolute inset-x-0 top-0 h-2"
          style={{
            backgroundImage:
              "repeating-linear-gradient(45deg,#facc15 0,#facc15 10px,#0d0d0b 10px,#0d0d0b 20px)",
          }}
          aria-hidden="true"
        />
        <div className="absolute inset-0 flex items-end p-6">
          <span className="text-[0.6rem] font-black uppercase tracking-[0.22em] text-yellow-400">
            {fallbackLabel}
          </span>
        </div>
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={decorative ? "" : alt}
      aria-hidden={decorative ? "true" : undefined}
      className={className}
      loading={loading}
      fetchPriority={fetchPriority}
      onError={() => setFailed(true)}
    />
  )
}
