"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import Image from "next/image";
import { Menu, X, ChevronDown, ChevronRight, Battery, Power, PlugZap, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { mainNavItems, type NavProductCategory, type NavSubCategory } from "@/data/navigation";
import Button from "@/components/ui/Button";
import ProductPlaceholder from "@/components/products/ProductPlaceholder";
import { motion, AnimatePresence } from "framer-motion";
import {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuTrigger,
  NavigationMenuContent,
  NavigationMenuLink,
} from "@/components/ui/navigation-menu";

const categoryIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  battery: Battery,
  power: Power,
  "plug-zap": PlugZap,
};

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [productsOpen, setProductsOpen] = useState(false);

  // Desktop dropdown state
  const [activeL1, setActiveL1] = useState<string | null>(null);

  // Mobile state
  const [mobileL1, setMobileL1] = useState<string | null>(null);
  const [mobileL2, setMobileL2] = useState<string | null>(null);

  // Navigate to a hash-based URL reliably (Next.js Link doesn't trigger hashchange on same page)
  const navigateToHash = useCallback((href: string) => {
    const [path, hash] = href.split("#");
    const targetPath = path || "/products";

    if (pathname === targetPath || pathname === targetPath + "/") {
      // Already on the same page — set hash directly and dispatch event
      window.location.hash = hash || "";
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    } else {
      // Different page — use router, hashchange will fire on mount
      router.push(href);
    }
  }, [pathname, router]);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [mobileOpen]);

  const linkClass = cn(
    "text-sm font-medium transition-all px-4 py-2 rounded-lg font-sans",
    scrolled
      ? "text-gray-600 hover:text-brand-600 hover:bg-brand-50"
      : "text-white/70 hover:text-white hover:bg-white/10"
  );

  // Resolve active data for the desktop 3-column panel
  const productsItem = mainNavItems.find((item) => item.productCategories);
  const categories = productsItem?.productCategories ?? [];
  const activeCategory = categories.find((c) => c.label === activeL1);

  return (
    <>
      <header
        className={cn(
          "fixed top-0 left-0 right-0 z-50 transition-all duration-500",
          scrolled
            ? "bg-white/80 backdrop-blur-xl border-b border-gray-200/50 shadow-[0_1px_20px_rgba(0,0,0,0.04)]"
            : "bg-transparent"
        )}
      >
        <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <Link href="/" className="flex items-center shrink-0 group">
              <Image
                src="/images/logo-transparent.png"
                alt="iTarang"
                width={120}
                height={40}
                className="h-8 w-auto object-contain"
                priority
              />
            </Link>

            {/* Desktop Navigation */}
            <NavigationMenu className="hidden lg:flex">
              <NavigationMenuList className="gap-0.5">
                {mainNavItems.map((item) =>
                  item.productCategories ? (
                    <NavigationMenuItem key={item.href}>
                      <NavigationMenuTrigger
                        className={cn(
                          "!bg-transparent !shadow-none text-sm font-medium font-sans px-4 py-2 rounded-lg transition-all",
                          scrolled
                            ? "text-gray-600 hover:text-brand-600 hover:bg-brand-50 data-[state=open]:text-brand-600 data-[state=open]:bg-brand-50"
                            : "text-white/70 hover:text-white hover:bg-white/10 data-[state=open]:text-white data-[state=open]:bg-white/10"
                        )}
                      >
                        {item.label}
                      </NavigationMenuTrigger>

                      {/* ── Trontek-style horizontal mega-menu ── */}
                      <NavigationMenuContent className="!w-[700px]">
                        <div className="bg-white rounded-xl">

                          {/* ─ Top row: category image cards ─ */}
                          <div className="px-6 pt-6 pb-4">
                            <div className="grid grid-cols-3 gap-5">
                              {categories.map((cat) => {
                                const isActive = activeL1 === cat.label;
                                return (
                                  <button
                                    key={cat.label}
                                    onClick={() => {
                                      navigateToHash(cat.href);
                                      setActiveL1(null);
                                    }}
                                    onMouseEnter={() => setActiveL1(cat.label)}
                                    className={cn(
                                      "group flex flex-col items-center rounded-xl p-4 border-2 transition-all duration-200 cursor-pointer",
                                      isActive
                                        ? "border-brand-500 bg-brand-50/40 shadow-sm"
                                        : "border-transparent hover:border-gray-200 bg-gray-50/50 hover:bg-gray-50"
                                    )}
                                  >
                                    {/* Image area */}
                                    <div className="w-full aspect-[5/4] rounded-lg flex items-center justify-center mb-3">
                                      {cat.image ? (
                                        <Image
                                          src={cat.image}
                                          alt={cat.label}
                                          width={120}
                                          height={96}
                                          className={cn(
                                            "w-[75%] h-auto object-contain transition-transform duration-300",
                                            isActive ? "scale-105" : "group-hover:scale-105"
                                          )}
                                        />
                                      ) : (
                                        <ProductPlaceholder
                                          type={cat.placeholderType ?? "battery"}
                                          className="w-[65%] h-[65%]"
                                        />
                                      )}
                                    </div>
                                    {/* Label */}
                                    <p className={cn(
                                      "text-[13px] font-bold text-center transition-colors",
                                      isActive ? "text-brand-600" : "text-gray-700 group-hover:text-gray-900"
                                    )}>
                                      {cat.label}
                                    </p>
                                  </button>
                                );
                              })}
                            </div>
                          </div>

                          {/* ─ Bottom row: variant pills for selected category ─ */}
                          <AnimatePresence mode="wait">
                            {activeCategory && (
                              <motion.div
                                key={activeL1}
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                transition={{ duration: 0.15 }}
                                className="overflow-hidden"
                              >
                                <div className="px-6 pb-5 pt-2">
                                  <div className="bg-gray-50 rounded-xl px-5 py-4">
                                    <div className="flex flex-wrap items-center gap-2">
                                      {activeCategory.subCategories.flatMap((sub) =>
                                        sub.variants.map((v) => (
                                          <NavigationMenuLink key={v.label} asChild>
                                            <a
                                              href={v.href}
                                              onClick={(e) => {
                                                e.preventDefault();
                                                navigateToHash(v.href);
                                              }}
                                              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-[13px] font-semibold text-gray-600 bg-white border border-gray-200 hover:border-brand-400 hover:bg-brand-50 hover:text-brand-600 transition-all duration-150 shadow-sm hover:shadow"
                                            >
                                              {v.label}
                                              {v.badge && (
                                                <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-full bg-brand-50 text-brand-500 border border-brand-200/60">
                                                  {v.badge}
                                                </span>
                                              )}
                                            </a>
                                          </NavigationMenuLink>
                                        ))
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>

                          {/* ─ Footer ─ */}
                          <div className="border-t border-gray-100 px-6 py-3 flex items-center justify-center">
                            <NavigationMenuLink asChild>
                              <a
                                href="/products"
                                onClick={(e) => {
                                  e.preventDefault();
                                  navigateToHash("/products");
                                }}
                                className="text-[11px] font-medium text-brand-500 hover:text-brand-700 transition-colors inline-flex items-center gap-1.5"
                              >
                                Explore all products <ArrowRight className="h-3 w-3" />
                              </a>
                            </NavigationMenuLink>
                          </div>

                        </div>
                      </NavigationMenuContent>
                    </NavigationMenuItem>
                  ) : (
                    <NavigationMenuItem key={item.href}>
                      <Link href={item.href} className={linkClass}>
                        {item.label}
                      </Link>
                    </NavigationMenuItem>
                  )
                )}
                <NavigationMenuItem>
                  <Link
                    href="/for-investors"
                    className={cn(
                      "text-sm font-medium transition-colors px-3 py-2 font-sans",
                      scrolled
                        ? "text-gray-400 hover:text-brand-600"
                        : "text-white/40 hover:text-white/70"
                    )}
                  >
                    For Investors
                  </Link>
                </NavigationMenuItem>
              </NavigationMenuList>
            </NavigationMenu>

            {/* CTA + Mobile toggle */}
            <div className="flex items-center gap-3">
              <div className="hidden lg:block">
                <Button href="/contact" size="sm" className={cn(
                  !scrolled && "bg-white/10 border border-white/20 text-white hover:bg-white/20 shadow-none"
                )}>
                  Talk to Us
                </Button>
              </div>
              <button
                onClick={() => setMobileOpen(true)}
                className={cn(
                  "lg:hidden p-2 rounded-lg transition-colors",
                  scrolled ? "text-gray-700 hover:bg-gray-100" : "text-white hover:bg-white/10"
                )}
                aria-label="Open menu"
              >
                <Menu className="h-5 w-5" />
              </button>
            </div>
          </div>
        </nav>
      </header>

      {/* ── Mobile menu ── */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm lg:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="fixed right-0 top-0 bottom-0 z-50 w-80 bg-white shadow-2xl lg:hidden overflow-y-auto"
            >
              <div className="flex items-center justify-between p-4 border-b border-gray-100">
                <Link href="/" className="flex items-center" onClick={() => setMobileOpen(false)}>
                  <Image
                    src="/images/logo-transparent.png"
                    alt="iTarang"
                    width={100}
                    height={32}
                    className="h-7 w-auto object-contain"
                  />
                </Link>
                <button onClick={() => setMobileOpen(false)} className="p-2 text-gray-400 hover:text-gray-600 rounded-lg">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <div className="p-4 space-y-1">
                {mainNavItems.map((item, i) => (
                  <motion.div
                    key={item.href}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    {item.productCategories ? (
                      <>
                        {/* Products toggle */}
                        <button
                          onClick={() => setProductsOpen(!productsOpen)}
                          className="flex items-center justify-between w-full px-4 py-3 text-base font-medium text-gray-700 hover:text-brand-600 hover:bg-brand-50 rounded-xl transition-colors font-sans"
                        >
                          {item.label}
                          <ChevronDown className={cn(
                            "h-4 w-4 text-gray-400 transition-transform duration-200",
                            productsOpen && "rotate-180 text-brand-500"
                          )} />
                        </button>

                        {/* L1 categories */}
                        <AnimatePresence>
                          {productsOpen && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: "auto", opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              transition={{ duration: 0.2 }}
                              className="overflow-hidden"
                            >
                              <div className="pl-2 pb-2 space-y-0.5">
                                {item.productCategories.map((cat) => {
                                  const Icon = categoryIcons[cat.icon] ?? Battery;
                                  const isL1Open = mobileL1 === cat.label;

                                  return (
                                    <div key={cat.label}>
                                      {/* L1 row */}
                                      <button
                                        onClick={() => { setMobileL1(isL1Open ? null : cat.label); setMobileL2(null); }}
                                        className={cn(
                                          "flex items-center justify-between w-full gap-3 px-3 py-2.5 text-sm font-medium rounded-lg transition-colors font-sans",
                                          isL1Open ? "text-brand-600 bg-brand-50" : "text-gray-600 hover:text-brand-600 hover:bg-brand-50"
                                        )}
                                      >
                                        <div className="flex items-center gap-3 min-w-0">
                                          <div className={cn(
                                            "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                                            isL1Open ? "bg-brand-100" : "bg-gray-50"
                                          )}>
                                            {cat.image ? (
                                              <Image src={cat.image} alt={cat.label} width={28} height={28} className="w-6 h-6 object-contain" />
                                            ) : (
                                              <Icon className={cn("h-4 w-4", isL1Open ? "text-brand-600" : "text-gray-400")} />
                                            )}
                                          </div>
                                          <span className="font-semibold text-[13px]">{cat.label}</span>
                                        </div>
                                        <ChevronRight className={cn(
                                          "h-3.5 w-3.5 text-gray-300 transition-transform duration-200 shrink-0",
                                          isL1Open && "rotate-90 text-brand-500"
                                        )} />
                                      </button>

                                      {/* L2 sub-categories */}
                                      <AnimatePresence>
                                        {isL1Open && (
                                          <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: "auto", opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            transition={{ duration: 0.15 }}
                                            className="overflow-hidden"
                                          >
                                            <div className="pl-11 pr-2 pt-1 pb-1 space-y-0.5">
                                              {cat.subCategories.map((sub) => {
                                                const isL2Open = mobileL2 === sub.label;
                                                return (
                                                  <div key={sub.label}>
                                                    <button
                                                      onClick={() => setMobileL2(isL2Open ? null : sub.label)}
                                                      className={cn(
                                                        "flex items-center justify-between w-full px-3 py-2 rounded-md text-[12px] font-semibold transition-colors",
                                                        isL2Open ? "text-brand-600 bg-brand-50" : "text-gray-500 hover:text-brand-600 hover:bg-gray-50"
                                                      )}
                                                    >
                                                      {sub.label}
                                                      <ChevronDown className={cn(
                                                        "h-3 w-3 transition-transform duration-200",
                                                        isL2Open && "rotate-180 text-brand-500"
                                                      )} />
                                                    </button>

                                                    {/* L3 variants */}
                                                    <AnimatePresence>
                                                      {isL2Open && (
                                                        <motion.div
                                                          initial={{ height: 0, opacity: 0 }}
                                                          animate={{ height: "auto", opacity: 1 }}
                                                          exit={{ height: 0, opacity: 0 }}
                                                          transition={{ duration: 0.12 }}
                                                          className="overflow-hidden"
                                                        >
                                                          <div className="pl-3 pr-1 py-1 flex flex-wrap gap-1.5">
                                                            {sub.variants.map((v) => (
                                                              <a
                                                                key={v.label}
                                                                href={v.href}
                                                                onClick={(e) => {
                                                                  e.preventDefault();
                                                                  setMobileOpen(false);
                                                                  navigateToHash(v.href);
                                                                }}
                                                                className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-[11px] font-semibold text-gray-500 bg-gray-50 border border-gray-200 hover:bg-brand-50 hover:text-brand-600 hover:border-brand-300 transition-all"
                                                              >
                                                                {v.label}
                                                                {v.badge && (
                                                                  <span className="text-[8px] font-bold text-brand-500 bg-brand-50 px-1 rounded">
                                                                    {v.badge}
                                                                  </span>
                                                                )}
                                                              </a>
                                                            ))}
                                                          </div>
                                                        </motion.div>
                                                      )}
                                                    </AnimatePresence>
                                                  </div>
                                                );
                                              })}
                                            </div>
                                          </motion.div>
                                        )}
                                      </AnimatePresence>
                                    </div>
                                  );
                                })}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </>
                    ) : (
                      <Link
                        href={item.href}
                        onClick={() => setMobileOpen(false)}
                        className="block px-4 py-3 text-base font-medium text-gray-700 hover:text-brand-600 hover:bg-brand-50 rounded-xl transition-colors font-sans"
                      >
                        {item.label}
                      </Link>
                    )}
                  </motion.div>
                ))}
                <div className="pt-4 border-t border-gray-100 mt-4 space-y-2">
                  <Link
                    href="/for-investors"
                    onClick={() => setMobileOpen(false)}
                    className="block px-4 py-3 text-sm font-medium text-gray-500 hover:text-brand-600 rounded-xl font-sans"
                  >
                    For Investors
                  </Link>
                  <Link
                    href="/blog"
                    onClick={() => setMobileOpen(false)}
                    className="block px-4 py-3 text-sm font-medium text-gray-500 hover:text-brand-600 rounded-xl font-sans"
                  >
                    Blog
                  </Link>
                </div>
                <div className="pt-4">
                  <Button href="/contact" size="md" className="w-full justify-center">
                    Talk to Us
                  </Button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
