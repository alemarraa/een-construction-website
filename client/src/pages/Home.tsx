import Header from "@/components/layout/Header"
import Footer from "@/components/layout/Footer"
import MobileActionBar from "@/components/layout/MobileActionBar"
import Hero from "@/components/sections/Hero"
import TrustStrip from "@/components/sections/TrustStrip"
import AudienceSection from "@/components/sections/AudienceSection"
import ServicesGrid from "@/components/sections/ServicesGrid"
import WhyEEN from "@/components/sections/WhyEEN"
import ProcessSection from "@/components/sections/ProcessSection"
import WorkStandard from "@/components/sections/WorkStandard"
import ServiceAreaSection from "@/components/sections/ServiceAreaSection"
import FAQSection from "@/components/sections/FAQSection"
import LeadForm from "@/components/sections/LeadForm"

export default function Home() {
  return (
    <>
      <Header />
      <main id="main-content" tabIndex={-1}>
        <Hero />
        <TrustStrip />
        <AudienceSection />
        <ServicesGrid />
        <WhyEEN />
        <ProcessSection />
        <WorkStandard />
        <ServiceAreaSection />
        <FAQSection />
        <LeadForm />
      </main>
      <Footer />
      <MobileActionBar />
    </>
  )
}
