import { submitPair } from "@/lib/server/audience";
import { requireUser } from "@/lib/server/auth";
import { store } from "@/lib/server/firebase-admin";
import { EVENT_ID, readJson, respond } from "@/lib/server/http";

/** POST /api/pairs — contribute a Gen Z <-> parents pair (becomes origin=human once approved). */
export async function POST(req: Request) {
  return respond(async () => {
    const user = await requireUser(req);
    return submitPair({ store, uid: user.uid, event: EVENT_ID(), now: Date.now() }, await readJson(req));
  });
}
