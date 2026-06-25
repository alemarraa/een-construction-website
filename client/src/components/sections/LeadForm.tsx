import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { Button } from "@/components/ui/button"
import { BUSINESS } from "@/config"
import { IMAGES } from "@/data/images"
import { Phone, Mail, CheckCircle2, AlertCircle, Loader2 } from "lucide-react"

const schema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Enter a valid email address"),
  phone: z.string().min(7, "Enter a valid phone number").optional().or(z.literal("")),
  unitCount: z.string().min(1, "Please select a unit count"),
  address: z.string().min(5, "Enter a property address"),
  workNeeded: z.string().min(10, "Briefly describe the work needed (min 10 characters)"),
  preferredContact: z.enum(["email", "phone", "either"]),
})

type FormData = z.infer<typeof schema>
type Status = "idle" | "loading" | "success" | "error"

export default function LeadForm() {
  const [status, setStatus] = useState<Status>("idle")

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { preferredContact: "either" },
  })

  const onSubmit = async (data: FormData) => {
    setStatus("loading")

    const formspreeId = import.meta.env.VITE_FORMSPREE_ID

    // In a production build without the secret configured, bail immediately.
    // This prevents a misleading 404 to /api/contact on static hosting.
    if (!formspreeId && import.meta.env.PROD) {
      setStatus("error")
      return
    }

    const endpoint = formspreeId
      ? `https://formspree.io/f/${formspreeId}`
      : "/api/contact" // local-dev Express fallback only

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setStatus("success")
      reset()
    } catch {
      setStatus("error")
    }
  }

  return (
    <section
      id="contact"
      className="scroll-mt-20 relative overflow-hidden bg-[#0d0d0b] py-24 lg:py-32"
      aria-labelledby="contact-heading"
    >
      {/* Blueprint bg */}
      <div
        className="pointer-events-none absolute inset-0 opacity-50"
        style={{ backgroundImage: `url(${IMAGES.blueprint})`, backgroundSize: "cover", backgroundPosition: "center" }}
        aria-hidden="true"
      />
      {/* Dark overlay */}
      <div className="pointer-events-none absolute inset-0 bg-[#0d0d0b]/78" aria-hidden="true" />

      <div className="container relative z-10">
        <div className="grid gap-16 lg:grid-cols-2 lg:gap-20">
          {/* ── LEFT: Context ── */}
          <div className="flex flex-col justify-center">
            <p className="mb-4 text-xs font-black uppercase tracking-[0.22em] text-yellow-400">Get Started</p>
            <h2
              id="contact-heading"
              className="mb-6 font-display text-4xl font-black uppercase leading-[0.92] tracking-tight text-white sm:text-5xl lg:text-6xl"
            >
              Unit Vacant?
              <br />
              <span className="text-yellow-400">Let&rsquo;s Get It</span>
              <br />
              Rent-Ready.
            </h2>
            <p className="mb-10 max-w-sm text-base font-semibold leading-8 text-stone-300">
              Submit your request and we'll follow up within one business day to schedule a walkthrough. The more detail you provide, the faster we can give you a preliminary scope.
            </p>

            <div className="flex flex-col gap-5">
              <a
                href={BUSINESS.phoneTel}
                className="group flex items-center gap-4 border border-white/10 bg-white/[0.05] p-5 backdrop-blur-sm hover:border-yellow-400/40 hover:bg-yellow-400/8 transition-all duration-200 shadow-[4px_4px_0_rgba(0,0,0,0.3)]"
                aria-label={`Call EEN Construction at ${BUSINESS.phone}`}
              >
                <span className="flex h-12 w-12 flex-shrink-0 items-center justify-center bg-yellow-400">
                  <Phone className="h-5 w-5 text-black" aria-hidden="true" />
                </span>
                <span>
                  <span className="block text-[0.6rem] font-black uppercase tracking-[0.2em] text-stone-500">Call Direct</span>
                  <span className="block text-xl font-black text-white">{BUSINESS.phone}</span>
                </span>
              </a>

              <a
                href={BUSINESS.gmailComposeUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center gap-4 border border-white/10 bg-white/[0.05] p-5 backdrop-blur-sm hover:border-yellow-400/40 hover:bg-yellow-400/8 transition-all duration-200 shadow-[4px_4px_0_rgba(0,0,0,0.3)]"
                aria-label={`Email ${BUSINESS.email}`}
              >
                <span className="flex h-12 w-12 flex-shrink-0 items-center justify-center bg-white/10">
                  <Mail className="h-5 w-5 text-yellow-400" aria-hidden="true" />
                </span>
                <span>
                  <span className="block text-[0.6rem] font-black uppercase tracking-[0.2em] text-stone-500">Email</span>
                  <span className="block text-sm font-semibold text-stone-300 break-all">{BUSINESS.email}</span>
                </span>
              </a>
            </div>
          </div>

          {/* ── RIGHT: Form ── */}
          <div className="border border-white/10 bg-[#0d0d0b]/80 p-8 shadow-[12px_12px_0_rgba(229,170,0,0.1)] backdrop-blur-md sm:p-10">
            {status === "success" ? (
              <div className="flex flex-col items-start gap-5">
                <div className="flex h-14 w-14 items-center justify-center bg-yellow-400">
                  <CheckCircle2 className="h-7 w-7 text-black" aria-hidden="true" />
                </div>
                <h3 className="font-display text-2xl font-black uppercase text-white">Request Received</h3>
                <p className="text-sm font-semibold leading-7 text-stone-400">
                  We'll follow up within one business day using your preferred contact method. If you included a property address and unit count, we may be able to send a preliminary scope before the walkthrough.
                </p>
                <button
                  onClick={() => setStatus("idle")}
                  className="text-xs font-black uppercase tracking-[0.16em] text-yellow-400 underline hover:no-underline"
                >
                  Submit another request
                </button>
              </div>
            ) : (
              <form
                onSubmit={handleSubmit(onSubmit)}
                noValidate
                aria-label="Unit turnaround request form"
                className="flex flex-col gap-5"
              >
                {status === "error" && (
                  <div role="alert" className="flex items-start gap-3 border border-red-500/30 bg-red-500/10 p-4">
                    <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-400" aria-hidden="true" />
                    <p className="text-sm font-semibold text-red-300">
                      Something went wrong. Please call{" "}
                      <a href={BUSINESS.phoneTel} className="underline">{BUSINESS.phone}</a>.
                    </p>
                  </div>
                )}

                <div className="grid gap-5 sm:grid-cols-2">
                  <Field label="Your Name" error={errors.name?.message} required>
                    <input {...register("name")} id="field-name" type="text" autoComplete="name" placeholder="Jane Smith" className="form-input" aria-required="true" />
                    {errors.name && <FieldError id="error-name" message={errors.name.message!} />}
                  </Field>
                  <Field label="Email Address" error={errors.email?.message} required>
                    <input {...register("email")} id="field-email" type="email" autoComplete="email" placeholder="you@example.com" className="form-input" aria-required="true" />
                    {errors.email && <FieldError id="error-email" message={errors.email.message!} />}
                  </Field>
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  <Field label="Phone Number" error={errors.phone?.message}>
                    <input {...register("phone")} id="field-phone" type="tel" autoComplete="tel" placeholder="(202) 555-0100" className="form-input" />
                    {errors.phone && <FieldError id="error-phone" message={errors.phone.message!} />}
                  </Field>
                  <Field label="Unit Count" error={errors.unitCount?.message} required>
                    <select {...register("unitCount")} id="field-unitCount" className="form-input" aria-required="true">
                      <option value="">Select unit count...</option>
                      <option value="4-10">4 - 10 units</option>
                      <option value="11-25">11 - 25 units</option>
                      <option value="26-50">26 - 50 units</option>
                      <option value="51+">51+ units</option>
                    </select>
                    {errors.unitCount && <FieldError id="error-unitCount" message={errors.unitCount.message!} />}
                  </Field>
                </div>

                <Field label="Property Address" error={errors.address?.message} required>
                  <input {...register("address")} id="field-address" type="text" autoComplete="street-address" placeholder="123 Main St, Baltimore, MD 21201" className="form-input" aria-required="true" />
                  {errors.address && <FieldError id="error-address" message={errors.address.message!} />}
                </Field>

                <Field label="Work Needed" error={errors.workNeeded?.message} required>
                  <textarea {...register("workNeeded")} id="field-workNeeded" rows={4} placeholder="Describe the vacant units and what needs to be done..." className="form-input resize-none" aria-required="true" />
                  {errors.workNeeded && <FieldError id="error-workNeeded" message={errors.workNeeded.message!} />}
                </Field>

                <fieldset>
                  <legend className="mb-3 block text-xs font-black uppercase tracking-[0.14em] text-stone-400">
                    Preferred Contact Method
                  </legend>
                  <div className="flex flex-wrap gap-4">
                    {[
                      { value: "either", label: "Either" },
                      { value: "email", label: "Email" },
                      { value: "phone", label: "Phone" },
                    ].map((opt) => (
                      <label key={opt.value} className="flex cursor-pointer items-center gap-2">
                        <input {...register("preferredContact")} type="radio" value={opt.value} className="accent-yellow-400 h-4 w-4" />
                        <span className="text-sm font-semibold text-stone-300">{opt.label}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>

                <Button
                  type="submit"
                  disabled={status === "loading"}
                  className="industrial-button mt-2 h-14 w-full rounded-none text-sm font-black uppercase tracking-[0.14em] disabled:opacity-60"
                >
                  {status === "loading" ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                      Sending...
                    </span>
                  ) : (
                    "Request Walkthrough"
                  )}
                </Button>

                <p className="text-center text-xs font-semibold text-stone-600">
                  We respond within one business day. 4+ unit properties only.
                </p>
                <p className="text-center text-[0.65rem] leading-5 text-stone-700">
                  Your information is used solely to respond to your request and will never be sold or shared with third parties.
                </p>
              </form>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}

function Field({ label, error, required, children }: {
  label: string; error?: string; required?: boolean; children: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-black uppercase tracking-[0.14em] text-stone-400">
        {label}
        {required && <span className="ml-1 text-yellow-400" aria-hidden="true">*</span>}
        {required && <span className="sr-only"> (required)</span>}
      </label>
      {children}
    </div>
  )
}

function FieldError({ id, message }: { id: string; message: string }) {
  return <p id={id} role="alert" className="text-xs font-semibold text-red-400">{message}</p>
}
