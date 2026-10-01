import type { Metadata } from "next";

import { AdminApp } from "@/components/admin/AdminApp";

export const metadata: Metadata = { title: "Genlingo · Consola del presentador", robots: { index: false } };

export default function AdminPage() {
  return <AdminApp />;
}
