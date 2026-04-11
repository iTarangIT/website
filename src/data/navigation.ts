export interface NavVariant {
  label: string;
  href: string;
  badge?: string;
}

export interface NavSubCategory {
  label: string;
  href: string;
  variants: NavVariant[];
}

export interface NavProductCategory {
  label: string;
  href: string;
  description: string;
  icon: "battery" | "power" | "plug-zap";
  image?: string;
  placeholderType?: "battery" | "inverter" | "charger";
  subCategories: NavSubCategory[];
}

export interface NavItem {
  label: string;
  href: string;
  productCategories?: NavProductCategory[];
}

export const mainNavItems: NavItem[] = [
  {
    label: "Products",
    href: "/products",
    productCategories: [
      {
        label: "Lithium-ion Battery",
        href: "/products#3-wheeler-batteries",
        description: "LiFePO4 batteries for e-rickshaws and 3-wheelers",
        icon: "battery",
        image: "/images/itarang battery.png",
        placeholderType: "battery",
        subCategories: [
          {
            label: "3W",
            href: "/products#3-wheeler-batteries",
            variants: [
              { label: "51V 105AH", href: "/products#3-wheeler-batteries:er-51v-105ah", badge: "Popular" },
              { label: "51V 132AH", href: "/products#3-wheeler-batteries:er-51v-132ah" },
              { label: "51V 153AH", href: "/products#3-wheeler-batteries:er-51v-153ah" },
              { label: "51V 232AH", href: "/products#3-wheeler-batteries:er-51v-232ah", badge: "Max Range" },
              { label: "61V 105AH", href: "/products#3-wheeler-batteries:er-61v-105ah" },
              { label: "61V 132AH", href: "/products#3-wheeler-batteries:er-61v-132ah", badge: "Best Seller" },
              { label: "61V 153AH", href: "/products#3-wheeler-batteries:er-61v-153ah" },
              { label: "61V 232AH", href: "/products#3-wheeler-batteries:er-61v-232ah", badge: "Premium" },
              { label: "64V 105AH", href: "/products#3-wheeler-batteries:er-64v-105ah" },
              { label: "64V 132AH", href: "/products#3-wheeler-batteries:er-64v-132ah" },
              { label: "72V 232AH", href: "/products#3-wheeler-batteries:er-72v-232ah", badge: "Max Power" },
            ],
          },
        ],
      },
      {
        label: "Inverter",
        href: "/products#inverters",
        description: "Pure sine wave inverters with smart monitoring",
        icon: "power",
        image: "/images/invertor.jpeg",
        placeholderType: "inverter",
        subCategories: [
          {
            label: "Pure Sine Wave",
            href: "/products#inverters",
            variants: [
              { label: "1KW", href: "/products#inverters:inv-1kw" },
              { label: "2KW", href: "/products#inverters:inv-2kw", badge: "Best Seller" },
              { label: "3KW", href: "/products#inverters:inv-3kw", badge: "Premium" },
            ],
          },
        ],
      },
      {
        label: "Charger",
        href: "/products#chargers",
        description: "Smart EV chargers with multi-voltage support",
        icon: "plug-zap",
        image: "/images/charger.png",
        placeholderType: "charger",
        subCategories: [
          {
            label: "EV Chargers",
            href: "/products#chargers",
            variants: [
              { label: "48V 15A", href: "/products#chargers:chg-48v-15a" },
              { label: "60V 20A", href: "/products#chargers:chg-60v-20a", badge: "Best Seller" },
              { label: "72V 25A", href: "/products#chargers:chg-72v-25a", badge: "Fleet Grade" },
            ],
          },
        ],
      },
    ],
  },
  { label: "How It Works", href: "/how-it-works" },
  { label: "For Partners", href: "/for-partners" },
  { label: "About", href: "/about" },
  { label: "Contact", href: "/contact" },
];
