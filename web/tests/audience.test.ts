import { describe, expect, it } from "vitest";

import { castVote, listQueue, reviewItem, submitPair, submitPhrase } from "../lib/server/audience";
import { blockedReason, normalize } from "../lib/server/blocklist";
import { decide } from "../lib/server/rate-limit";
import { MemoryStore } from "../lib/server/store";

const ctx = (store: MemoryStore, now = 1_000_000, uid = "u1") => ({ store, uid, event: "gdg", now });
const phrase = { text: "no manches, está bien mid", direction: "genz_to_parent", country: "MX" };

describe("rate limit (20 s)", () => {
  it("allows the first submission and blocks for 20 s", () => {
    expect(decide(undefined, 0)).toEqual({ ok: true });
    expect(decide(0, 5_000)).toEqual({ ok: false, retryAfterMs: 15_000 });
    expect(decide(0, 20_000)).toEqual({ ok: true });
  });

  it("is enforced by the server per person, not per request", async () => {
    const store = new MemoryStore();
    expect((await submitPhrase(ctx(store), phrase)).status).toBe(201);
    const second = await submitPhrase(ctx(store, 1_010_000), phrase);
    expect(second.status).toBe(429);
    expect(second.body.error).toMatch(/Espera 10 segundos/);
    expect((await submitPhrase(ctx(store, 1_010_000, "u2"), phrase)).status).toBe(201); // another phone
    expect((await submitPhrase(ctx(store, 1_020_000), phrase)).status).toBe(201);
  });

  it("phrases and pairs share the window", async () => {
    const store = new MemoryStore();
    await submitPhrase(ctx(store), phrase);
    const pair = { source: "qué oso", target: "qué vergüenza", direction: "genz_to_parent", country: "MX" };
    expect((await submitPair(ctx(store, 1_005_000), pair)).status).toBe(429);
  });

  it("invalid input does not burn the window", async () => {
    const store = new MemoryStore();
    expect((await submitPhrase(ctx(store), { ...phrase, direction: "x" })).status).toBe(400);
    expect((await submitPhrase(ctx(store, 1_000_500), phrase)).status).toBe(201);
  });
});

describe("blocklist", () => {
  it("blocks insults even with tricks, keeps normal slang", () => {
    expect(blockedReason("eres un p3nd3j00")).toBe("lenguaje");
    expect(blockedReason("hijo de puta")).toBe("lenguaje");
    expect(blockedReason("PUUUUTO")).toBe("lenguaje");
    expect(blockedReason("no manches, está bien chilero")).toBeNull();
    expect(blockedReason("qué pena con usted, el perro se comió la pera")).toBeNull();
  });

  it("blocks personal data on the public screen", () => {
    expect(blockedReason("sígueme en @fulanito")).toBe("usuario");
    expect(blockedReason("mira www.ejemplo.com")).toBe("enlace");
    expect(blockedReason("llámame al 5555 1234")).toBe("teléfono");
  });

  it("normalizes accents but keeps ñ", () => {
    expect(normalize("Qué Coño")).toBe("que coño");
  });

  it("blocked phrases never reach the queue", async () => {
    const store = new MemoryStore();
    const r = await submitPhrase(ctx(store), { ...phrase, text: "qué pendejo" });
    expect(r.status).toBe(422);
    expect(store.phrases.size).toBe(0);
  });
});

describe("validation", () => {
  it("rejects phrases over 30 words", async () => {
    const r = await submitPhrase(ctx(new MemoryStore()), { ...phrase, text: Array(31).fill("x").join(" ") });
    expect(r.status).toBe(400);
    expect(r.body.error).toMatch(/30 palabras/);
  });

  it("rejects identical pairs", async () => {
    const r = await submitPair(ctx(new MemoryStore()), { source: "hola", target: "Hola", direction: "genz_to_parent", country: "GT" });
    expect(r.status).toBe(400);
  });
});

describe("votes", () => {
  it("one vote per person per open round of this event", async () => {
    const store = new MemoryStore();
    store.rounds.set("r1", { event: "gdg", phrase: "x", direction: "genz_to_parent", country: "MX", david: "a", goliath: "b", roundType: "audience", status: "voting" });
    store.rounds.set("r2", { ...store.rounds.get("r1")!, status: "closed" });
    expect((await castVote(ctx(store), { roundId: "r1", choice: "david" })).status).toBe(201);
    expect((await castVote(ctx(store), { roundId: "r1", choice: "goliath" })).status).toBe(409);
    expect((await castVote(ctx(store), { roundId: "r2", choice: "david" })).status).toBe(409);
    expect((await castVote(ctx(store), { roundId: "nope", choice: "david" })).status).toBe(404);
    expect((await castVote(ctx(store), { roundId: "r1", choice: "nadie" })).status).toBe(400);
  });
});

describe("auto-approve (no moderator needed)", () => {
  it("approves blocklist-clean phrases at once and still blocks the rest", async () => {
    const store = new MemoryStore();
    const ok = await submitPhrase({ ...ctx(store), autoApprove: true }, phrase);
    expect(ok.body.status).toBe("approved");
    expect(store.phrases.get(ok.body.id as string)?.approvedAt).toBe(1_000_000);
    const bad = await submitPhrase({ ...ctx(store, 1_030_000), autoApprove: true }, { ...phrase, text: "qué pendejo" });
    expect(bad.status).toBe(422);
  });
});

describe("presenter review", () => {
  it("approving moves a phrase out of the pending queue", async () => {
    const store = new MemoryStore();
    const { body } = await submitPhrase(ctx(store), phrase);
    expect(((await listQueue(ctx(store), "phrases")).body.items as unknown[]).length).toBe(1);
    expect((await reviewItem(ctx(store), "phrases", body.id as string, { action: "approve" })).status).toBe(200);
    expect(((await listQueue(ctx(store), "phrases")).body.items as unknown[]).length).toBe(0);
    expect(store.phrases.get(body.id as string)?.approvedAt).toBe(1_000_000);
  });
});
