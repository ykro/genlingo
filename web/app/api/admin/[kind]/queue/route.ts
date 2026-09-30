import { listQueue } from "@/lib/server/audience";
import { requireAdmin } from "@/lib/server/auth";
import { store } from "@/lib/server/firebase-admin";
import { EVENT_ID, respond } from "@/lib/server/http";

/** GET /api/admin/phrases/queue | /api/admin/pairs/queue — pending items for the presenter. */
export async function GET(req: Request, { params }: { params: Promise<{ kind: string }> }) {
  const { kind } = await params;
  if (kind !== "phrases" && kind !== "pairs") return Response.json({ error: "No encontrado." }, { status: 404 });
  return respond(async () => {
    const user = await requireAdmin(req);
    return listQueue({ store, uid: user.uid, event: EVENT_ID(), now: Date.now() }, kind);
  });
}
