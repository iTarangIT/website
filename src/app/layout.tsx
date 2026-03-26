import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrains = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "iTarang Technologies | The Intelligence Layer for India's EV Battery Economy",
  description:
    "India's 1st EV Battery Financing & Lifecycle Management Ecosystem. Turning batteries into programmable financial assets through smart telemetry, behavioral risk scoring, and lifecycle intelligence.",
  openGraph: {
    title: "iTarang Technologies",
    description: "The Intelligence Layer for India's EV Battery Economy",
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
    <html lang="en" className={`${inter.variable} ${jetbrains.variable}`}>
      <body className="min-h-screen flex flex-col antialiased">{children}</body>
    </html>
  );
}
