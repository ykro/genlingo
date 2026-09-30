import { submitPhrase } from "@/lib/server/audience";
import { requireUser } from "@/lib/server/auth";
import { store } from "@/lib/server/firebase-admin";
import { EVENT_ID, readJson, respond } from "@/lib/server/http";

/** POST /api/phrases — send a phrase for the duel (queued for the presenter's approval). */
export async function POST(req: Request) {
  return respond(async () => {
    const user = await requireUser(req);
    return submitPhrase({ store, uid: user.uid, event: EVENT_ID(), now: Date.now() }, await readJson(req));
  });
}
