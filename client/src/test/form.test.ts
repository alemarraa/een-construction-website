import { describe, expect, it } from "vitest"
import { z } from "zod"

const schema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Enter a valid email address"),
  phone: z.string().min(7, "Enter a valid phone number").optional().or(z.literal("")),
  unitCount: z.string().min(1, "Please select a unit count"),
  address: z.string().min(5, "Enter a property address"),
  workNeeded: z.string().min(10, "Briefly describe the work needed (min 10 characters)"),
  preferredContact: z.enum(["email", "phone", "either"]),
})

const validPayload = {
  name: "Jane Smith",
  email: "jane@example.com",
  phone: "",
  unitCount: "4-10",
  address: "123 Main St, Silver Spring, MD",
  workNeeded: "Full unit turnaround — paint, drywall, and fixtures on 3 units",
  preferredContact: "either" as const,
}

describe("contact form schema", () => {
  it("accepts a complete valid submission", () => {
    expect(schema.safeParse(validPayload).success).toBe(true)
  })

  it("accepts an empty phone number", () => {
    expect(schema.safeParse({ ...validPayload, phone: "" }).success).toBe(true)
  })

  it("rejects invalid email", () => {
    const result = schema.safeParse({ ...validPayload, email: "not-an-email" })
    expect(result.success).toBe(false)
    if (!result.success) {
      const paths = result.error.issues.map((i) => i.path[0])
      expect(paths).toContain("email")
    }
  })

  it("rejects name shorter than 2 characters", () => {
    const result = schema.safeParse({ ...validPayload, name: "J" })
    expect(result.success).toBe(false)
  })

  it("rejects work description shorter than 10 characters", () => {
    const result = schema.safeParse({ ...validPayload, workNeeded: "Paint" })
    expect(result.success).toBe(false)
  })

  it("rejects missing unit count", () => {
    const result = schema.safeParse({ ...validPayload, unitCount: "" })
    expect(result.success).toBe(false)
  })

  it("rejects invalid preferredContact value", () => {
    const result = schema.safeParse({ ...validPayload, preferredContact: "fax" as never })
    expect(result.success).toBe(false)
  })
})
