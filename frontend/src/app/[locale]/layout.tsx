import type React from "react"
import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { Suspense } from "react"
import "@/app/globals.css"
import {NextIntlClientProvider, useMessages} from "next-intl";
import {pick} from "lodash";

const geistSans = Geist({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-geist-sans",
})

const geistMono = Geist_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-geist-mono",
})

interface LayoutProps {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
};

export const metadata: Metadata = {
  title: "Goodwill Central Texas - GenAI Referral Tool",
  description: "AI-powered referral tool for Goodwill Central Texas",
  generator: "v0.app",
}


export default async function RootLayout({children, params }: LayoutProps) {
  const {locale} = await params;
  return (
    <html lang={locale} className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
    <body className="font-sans">
    <Suspense fallback={null}>
      <NextIntlClientProvider locale={locale}>
        {children}
      </NextIntlClientProvider>
    </Suspense>
    </body>
    </html>
  )
}
