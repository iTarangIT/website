import type { Metadata } from "next";
import { DM_Serif_Display, Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const dmSerif = DM_Serif_Display({
  variable: "--font-display",
  subsets: ["latin"],
  weight: "400",
});

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-body",
  subsets: ["latin"],
});

const jetbrains = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://www.itarang.com"),
  title: "iTarang | Every Battery. From First Charge to Last.",
  description:
    "We finance, track, maintain, and recycle EV batteries across India. Drivers get affordable EMIs. Lenders get visibility. Nothing falls through the cracks.",
  openGraph: {
    title: "iTarang Technologies",
    description:
      "Every Battery. From First Charge to Last. EV battery lifecycle management across India.",
    url: "https://www.itarang.com",
    siteName: "iTarang Technologies",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${dmSerif.variable} ${jakarta.variable} ${jetbrains.variable}`}>
      <body className="min-h-screen flex flex-col antialiased">{children}</body>
    </html>
  );
}
