"use client";

import { motion } from "framer-motion";
import { UserPlus, Star } from "lucide-react";
import { founders, keyHires, advisors } from "@/data/team";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import Badge from "@/components/ui/Badge";
import { staggerContainer, staggerItem } from "@/lib/animations";

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export default function TeamSection() {
  return (
    <section className="py-20 md:py-28 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <SectionHeading
            badge="The Team"
            title="Built by Operators, Not Just Engineers"
            subtitle="A founding team that combines deep domain expertise in fintech, IoT, and India's EV ecosystem."
          />
        </FadeInOnScroll>

        {/* Founders */}
        <motion.div
          variants={staggerContainer}
          initial="initial"
          whileInView="animate"
          viewport={{ once: true, amount: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16"
        >
          {founders.map((founder) => (
            <motion.div
              key={`${founder.name}-${founder.role}`}
              variants={staggerItem}
              transition={{ duration: 0.5 }}
              className="rounded-2xl border border-gray-100 bg-white shadow-sm p-8 hover:shadow-lg transition-shadow duration-300"
            >
              <div className="flex items-start gap-5">
                {/* Avatar circle with initials */}
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-brand-700 shrink-0">
                  <span className="text-xl font-bold text-white">
                    {getInitials(founder.name)}
                  </span>
                </div>

                <div className="flex-1">
                  <h3 className="text-lg font-bold text-gray-900">
                    {founder.name}
                  </h3>
                  <Badge className="mt-1">{founder.role}</Badge>
                  <p className="mt-3 text-sm text-gray-600 leading-relaxed">
                    {founder.description}
                  </p>
                </div>
              </div>

              {/* Responsibilities */}
              <div className="mt-6 pt-5 border-t border-gray-100">
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
                  Key Responsibilities
                </p>
                <ul className="space-y-2">
                  {founder.responsibilities.map((resp, j) => (
                    <li
                      key={j}
                      className="flex items-center gap-2 text-sm text-gray-600"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-brand-400 shrink-0" />
                      {resp}
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Key Hires and Advisors - two columns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Key Hires Planned */}
          <FadeInOnScroll direction="left">
            <div className="rounded-2xl border border-gray-100 bg-white shadow-sm p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50">
                  <UserPlus className="h-5 w-5 text-brand-500" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">Key Hires Planned</h3>
                  <p className="text-xs text-gray-500">
                    First 12 months post-funding
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                {keyHires.map((hire) => (
                  <div
                    key={hire.role}
                    className="rounded-xl bg-gray-50 border border-gray-100 p-4"
                  >
                    <h4 className="font-semibold text-gray-900 text-sm">
                      {hire.role}
                    </h4>
                    <p className="mt-1 text-xs text-gray-500 leading-relaxed">
                      {hire.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </FadeInOnScroll>

          {/* Advisory Board */}
          <FadeInOnScroll direction="right">
            <div className="rounded-2xl border border-gray-100 bg-white shadow-sm p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-yellow/20">
                  <Star className="h-5 w-5 text-accent-yellow" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">Advisory Board</h3>
                  <p className="text-xs text-gray-500">
                    Domain experts guiding strategy
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                {advisors.map((advisor) => (
                  <div
                    key={advisor.title}
                    className="flex items-center gap-4 rounded-xl bg-gray-50 border border-gray-100 p-4"
                  >
                    {/* Placeholder avatar */}
                    <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-br from-brand-400 to-accent-sky shrink-0">
                      <span className="text-sm font-bold text-white">
                        {advisor.title[0]}
                      </span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 text-sm">
                        {advisor.title}
                      </h4>
                      <Badge variant="accent" className="mt-1">
                        {advisor.expertise}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 rounded-lg bg-brand-50 border border-brand-100">
                <p className="text-sm text-brand-700 font-medium">
                  Advisory board actively being expanded. Open to introductions
                  from investors.
                </p>
              </div>
            </div>
          </FadeInOnScroll>
        </div>
      </div>
    </section>
  );
}
