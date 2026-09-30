import "server-only";

import { FieldValue, type Firestore, Timestamp } from "firebase-admin/firestore";

import { COLLECTIONS, type Choice, type PairDoc, type PhraseDoc, type ReviewStatus, type RoundDoc } from "./model";
import { decide } from "./rate-limit";
import type { AudienceStore } from "./store";

const toMs = (v: unknown) => (v instanceof Timestamp ? v.toMillis() : typeof v === "number" ? v : undefined);

export class FirestoreStore implements AudienceStore {
  constructor(private db: Firestore) {}

  async claimSubmission(uid: string, nowMs: number) {
    const ref = this.db.collection(COLLECTIONS.rateLimits).doc(uid);
    return this.db.runTransaction(async (tx) => {
      const snap = await tx.get(ref);
      const d = decide(toMs(snap.get("lastSubmissionAt")), nowMs);
      if (d.ok) tx.set(ref, { lastSubmissionAt: Timestamp.fromMillis(nowMs) }, { merge: true });
      return d;
    });
  }

  async addPhrase(doc: PhraseDoc) {
    const ref = await this.db.collection(COLLECTIONS.phrases).add({ ...doc, createdAt: Timestamp.fromMillis(doc.createdAt) });
    return ref.id;
  }

  async addPair(doc: PairDoc) {
    const ref = await this.db.collection(COLLECTIONS.pairs).add({ ...doc, createdAt: Timestamp.fromMillis(doc.createdAt) });
    return ref.id;
  }

  async getRound(roundId: string) {
    const snap = await this.db.collection(COLLECTIONS.rounds).doc(roundId).get();
    return snap.exists ? (snap.data() as RoundDoc) : null;
  }

  async addVote(roundId: string, uid: string, choice: Choice, nowMs: number) {
    try {
      // create() fails if the doc exists: the doc id is the uid, so one vote per person.
      await this.db
        .collection(COLLECTIONS.rounds).doc(roundId)
        .collection(COLLECTIONS.votes).doc(uid)
        .create({ choice, createdAt: Timestamp.fromMillis(nowMs) });
      return true;
    } catch (err) {
      if ((err as { code?: number }).code === 6) return false; // ALREADY_EXISTS
      throw err;
    }
  }

  async listPending(kind: "phrases" | "pairs", event: string) {
    const snap = await this.db
      .collection(COLLECTIONS[kind])
      .where("event", "==", event)
      .where("status", "==", "pending")
      .orderBy("createdAt")
      .limit(100)
      .get();
    return snap.docs.map((d) => {
      const data = d.data();
      return { id: d.id, ...data, createdAt: toMs(data.createdAt) ?? 0 } as { id: string } & (PhraseDoc | PairDoc);
    });
  }

  async review(kind: "phrases" | "pairs", id: string, status: ReviewStatus) {
    const ref = this.db.collection(COLLECTIONS[kind]).doc(id);
    const snap = await ref.get();
    if (!snap.exists) return false;
    // approvedAt is what the duel service's feed orders the on-screen queue by.
    await ref.update({ status, ...(status === "approved" ? { approvedAt: FieldValue.serverTimestamp() } : {}) });
    return true;
  }
}
