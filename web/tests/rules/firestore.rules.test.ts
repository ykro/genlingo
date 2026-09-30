/**
 * Security rules, run against the Firestore emulator:
 *   npm run test:rules   (firebase emulators:exec --only firestore)
 */
import { readFileSync } from "node:fs";

import { assertFails, assertSucceeds, initializeTestEnvironment, type RulesTestEnvironment } from "@firebase/rules-unit-testing";
import { doc, getDoc, setDoc } from "firebase/firestore";
import { afterAll, beforeAll, describe, it } from "vitest";

let env: RulesTestEnvironment;

beforeAll(async () => {
  env = await initializeTestEnvironment({
    projectId: "demo-genlingo",
    firestore: { rules: readFileSync("firestore.rules", "utf8") },
  });
  await env.withSecurityRulesDisabled(async (ctx) => {
    const db = ctx.firestore();
    await setDoc(doc(db, "rounds/r1"), { event: "gdg", status: "voting" });
    await setDoc(doc(db, "phrases/p1"), { uid: "alice", text: "qué oso", status: "pending" });
    await setDoc(doc(db, "rounds/r1/votes/alice"), { choice: "david" });
  });
});

afterAll(async () => env?.cleanup());

describe("client writes are denied (the API enforces rate limit + blocklist)", () => {
  it("cannot write phrases, pairs, votes or rate limits directly", async () => {
    const db = env.authenticatedContext("alice").firestore();
    await assertFails(setDoc(doc(db, "phrases/x"), { uid: "alice", text: "hola", status: "approved" }));
    await assertFails(setDoc(doc(db, "pairs/x"), { uid: "alice", source: "a", target: "b" }));
    await assertFails(setDoc(doc(db, "rounds/r1/votes/alice"), { choice: "goliath" }));
    await assertFails(setDoc(doc(db, "rateLimits/alice"), { lastSubmissionAt: 0 }));
  });
});

describe("reads", () => {
  it("signed-in phones read the round on screen; anonymous visitors without auth can't", async () => {
    await assertSucceeds(getDoc(doc(env.authenticatedContext("bob").firestore(), "rounds/r1")));
    await assertFails(getDoc(doc(env.unauthenticatedContext().firestore(), "rounds/r1")));
  });

  it("you read your own phrase and vote, not other people's", async () => {
    await assertSucceeds(getDoc(doc(env.authenticatedContext("alice").firestore(), "phrases/p1")));
    await assertFails(getDoc(doc(env.authenticatedContext("bob").firestore(), "phrases/p1")));
    await assertSucceeds(getDoc(doc(env.authenticatedContext("alice").firestore(), "rounds/r1/votes/alice")));
    await assertFails(getDoc(doc(env.authenticatedContext("bob").firestore(), "rounds/r1/votes/alice")));
  });

  it("the presenter (admin claim) reads the queue", async () => {
    await assertSucceeds(getDoc(doc(env.authenticatedContext("presenter", { admin: true }).firestore(), "phrases/p1")));
  });
});
