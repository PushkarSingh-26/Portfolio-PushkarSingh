import { Hero } from "@/components/hero/Hero";
import { CapabilitiesSection } from "@/components/capabilities/CapabilitiesSection";
import { SigmaSection } from "@/components/sigma/SigmaSection";
import { AegisSection } from "@/components/aegis/AegisSection";
import { ExperienceSection } from "@/components/experience/ExperienceSection";
import { ResearchSection } from "@/components/research/ResearchSection";
import { MoreProjectsSection } from "@/components/projects/MoreProjectsSection";
import { RecognitionSection, EducationSection } from "@/components/sections/RecognitionSection";
import { ContactSection } from "@/components/sections/ContactSection";

/**
 * The narrative: identity → capabilities → the model (Sigma) → a grounded system
 * (AegisAI) → the path that led here → research → more projects → recognition → contact.
 */
export default function Home() {
  return (
    <>
      <Hero />
      <CapabilitiesSection />
      <SigmaSection />
      <AegisSection />
      <ExperienceSection />
      <ResearchSection />
      <MoreProjectsSection />
      <RecognitionSection />
      <EducationSection />
      <ContactSection />
    </>
  );
}
