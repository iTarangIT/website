import type { Metadata } from "next";
import Script from "next/script";
import { DM_Serif_Display, Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import ChatWidget from "@/components/chatbot/ChatWidget";
import GoogleAnalytics from "@/components/analytics/GoogleAnalytics";
import WhatsAppButton from "@/components/shared/WhatsAppButton";

const GTM_ID = "GTM-NWF4GDVS";

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
      <body className="min-h-screen flex flex-col antialiased">
        {/* Google Tag Manager (noscript) */}
        <noscript
          dangerouslySetInnerHTML={{
            __html: `<iframe src="https://www.googletagmanager.com/ns.html?id=${GTM_ID}" height="0" width="0" style="display:none;visibility:hidden"></iframe>`,
          }}
        />
        {/* End Google Tag Manager (noscript) */}
        <Script
          id="google-tag-manager"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','${GTM_ID}');`,
          }}
        />
        {children}
        <ChatWidget />
        <WhatsAppButton />
        <GoogleAnalytics />
      </body>
    </html>
  );
}
