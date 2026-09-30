import { reviewItem } from "@/lib/server/audience";
import { requireAdmin } from "@/lib/server/auth";
import { store } from "@/lib/server/firebase-admin";
import { EVENT_ID, readJson, respond } from "@/lib/server/http";

/** POST /api/admin/phrases/{id} | /api/admin/pairs/{id} — { action: "approve" | "reject" }. */
export async function POST(req: Request, { params }: { params: Promise<{ kind: string; id: string }> }) {
  const { kind, id } = await params;
  if (kind !== "phrases" && kind !== "pairs") return Response.json({ error: "No encontrado." }, { status: 404 });
  return respond(async () => {
    const user = await requireAdmin(req);
    return reviewItem({ store, uid: user.uid, event: EVENT_ID(), now: Date.now() }, kind, id, await readJson(req));
  });
}
