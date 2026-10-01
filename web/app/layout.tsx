import type { Metadata, Viewport } from "next";
import { Big_Shoulders, Figtree } from "next/font/google";
import type { ReactNode } from "react";

import "./globals.css";

// Fonts are downloaded at build time and served by the app itself: the presenter view keeps
// its typography with Wi-Fi off.
const display = Big_Shoulders({ subsets: ["latin"], weight: ["500", "600", "700", "800"], variable: "--font-display" });
const body = Figtree({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-body" });

export const metadata: Metadata = {
  title: "Genlingo",
  description: "David contra Goliat: un modelo pequeño traduce entre la Gen Z y sus papás.",
};

export const viewport: Viewport = { themeColor: "#f6f3ec", colorScheme: "light" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es" className={`${display.variable} ${body.variable}`}>
      <body>{children}</body>
    </html>
  );
}
