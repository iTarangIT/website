"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { productFaqs } from "@/data/products";

export default function FAQAccordion() {
    const [openIndex, setOpenIndex] = useState<number | null>(null);

    const toggleFAQ = (index: number) => {
        setOpenIndex(openIndex === index ? null : index);
    };

    return (
        <section className="py-16 md:py-24 bg-[#fcfcfc]">
            <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
                <h2 className="text-center font-sans text-3xl md:text-[40px] font-bold text-[#0a2540] mb-12">
                    Frequently asked questions
                </h2>

                <div className="space-y-4">
                    {productFaqs.map((faq, index) => {
                        const isOpen = openIndex === index;
                        return (
                            <div
                                key={index}
                                className="bg-transparent border-b border-gray-200 overflow-hidden"
                            >
                                <button
                                    onClick={() => toggleFAQ(index)}
                                    className="w-full flex items-center justify-between py-6 text-left focus:outline-none cursor-pointer group"
                                >
                                    <span className="font-sans text-[18px] md:text-[20px] font-bold text-[#0a2540] pr-8 group-hover:text-brand-600 transition-colors">
                                        {faq.question}
                                    </span>
                                    <ChevronDown
                                        className={`shrink-0 w-6 h-6 text-[#0a2540] transition-transform duration-300 ${isOpen ? "rotate-180 text-brand-500" : "opacity-60"}`}
                                    />
                                </button>
                                <AnimatePresence>
                                    {isOpen && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: "auto", opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            transition={{ duration: 0.3, ease: "easeInOut" }}
                                        >
                                            <div className="pb-8 font-sans text-base text-[#64748b] leading-relaxed max-w-3xl">
                                                {faq.answer}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        );
                    })}
                </div>
            </div>
        </section>
    );
}
