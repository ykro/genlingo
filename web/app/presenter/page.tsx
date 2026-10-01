import type { Metadata } from "next";

import { PresenterApp } from "@/components/presenter/PresenterApp";

export const metadata: Metadata = { title: "Genlingo · Duelo", robots: { index: false } };

/** Presenter view (stage screen, 1920×1080). Runs on the laptop next to the duel service. */
export default function PresenterPage() {
  return <PresenterApp />;
}
