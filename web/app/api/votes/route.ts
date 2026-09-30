import { castVote } from "@/lib/server/audience";
import { requireUser } from "@/lib/server/auth";
import { store } from "@/lib/server/firebase-admin";
import { EVENT_ID, readJson, respond } from "@/lib/server/http";

/** POST /api/votes — { roundId, choice: "david" | "goliath" }, one vote per person per round. */
export async function POST(req: Request) {
  return respond(async () => {
    const user = await requireUser(req);
    return castVote({ store, uid: user.uid, event: EVENT_ID(), now: Date.now() }, await readJson(req));
  });
}
