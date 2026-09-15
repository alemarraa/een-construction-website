// Site imagery is self-hosted from client/public/images so it ships with the
// build. Do not point these at an external CDN — the previous host expired and
// every photo on the site broke at once.
//
// To swap in a real photo: drop the file into client/public/images using the
// same name (or update the path here) and rebuild. If a file is missing, the
// SiteImage component renders a branded blueprint panel instead of a broken
// image icon.

export const IMAGES = {
  hero: "/images/hero-unit-turnaround.jpg",
  services: "/images/crew-turnaround.jpg",
  blueprint: "/images/blueprint-grid.svg",
  worker: "/images/tile-finish-detail.jpg",
} as const
