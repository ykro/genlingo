import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import type { ReactNode } from "react";

import "./globals.css";

// Fonts live in the repo (app/fonts, OFL) and are served by the app itself: the presenter view
// keeps its typography with Wi-Fi off, and builds never depend on fetching fonts.
const display = localFont({ src: "./fonts/BigShoulders-latin.woff2", weight: "500 800", variable: "--font-display", display: "swap" });
const body = localFont({ src: "./fonts/Figtree-latin.woff2", weight: "400 700", variable: "--font-body", display: "swap" });

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
