import { keyAdvantages } from "@/data/products";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

export default function KeyAdvantages() {
  return (
    <section className="p-8 md:p-12 bg-white">
      <div className="mx-auto max-w-5xl">
        <div className="text-center mb-8">
          <h2 className="font-sans text-2xl md:text-[30px] font-extrabold uppercase tracking-wide text-[#0a2540] mb-3">
            Why Choose <span className="text-[#ef6c00]">iTarang?</span>
          </h2>
          <p className="text-sm text-[#64748b] leading-relaxed max-w-2xl mx-auto font-sans">
            The safest and most durable lithium technology — engineered specifically for the harsh conditions of Indian commercial EVs.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4 mt-6">
          {keyAdvantages.map((advantage, i) => (
            <FadeInOnScroll key={advantage.title} delay={i * 0.05}>
              <div className="flex items-start gap-4 px-5 py-4 bg-[#f8fafc] border border-[#e2e8f4] rounded-lg transition-all duration-250 hover:bg-[#e0f0ff] hover:border-[#90c8f0] hover:translate-x-1 group">
                <div className="flex-shrink-0 w-2.5 h-2.5 mt-1.5 rounded-full bg-[#ef6c00] shadow-[0_0_6px_rgba(239,108,0,0.4)]" />
                <div className="flex-1 min-w-0">
                  <div className="font-sans text-[15px] font-bold text-[#0a2540] group-hover:text-[#1a6fa8] transition-colors">
                    {advantage.title}
                  </div>
                  <div className="font-sans text-[13px] text-[#64748b] leading-snug mt-1">
                    {advantage.description}
                  </div>
                </div>
              </div>
            </FadeInOnScroll>
          ))}
        </div>
      </div>
    </section>
  );
}
