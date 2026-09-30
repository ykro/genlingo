/**
 * Persistence behind the audience API. The Firestore implementation is what runs on Cloud
 * Run; the in-memory one lets the tests exercise the same rules (rate limit, one vote per
 * person, review flow) without network.
 */

import type { Choice, PairDoc, PhraseDoc, ReviewStatus, RoundDoc } from "./model";
import { decide, type RateDecision } from "./rate-limit";

export interface AudienceStore {
  /** Atomically check the 20 s window and, if allowed, record `nowMs` as the last submission. */
  claimSubmission(uid: string, nowMs: number): Promise<RateDecision>;
  addPhrase(doc: PhraseDoc): Promise<string>;
  addPair(doc: PairDoc): Promise<string>;
  getRound(roundId: string): Promise<RoundDoc | null>;
  /** false if this person already voted in this round. */
  addVote(roundId: string, uid: string, choice: Choice, nowMs: number): Promise<boolean>;
  listPending(kind: "phrases" | "pairs", event: string): Promise<Array<{ id: string } & (PhraseDoc | PairDoc)>>;
  review(kind: "phrases" | "pairs", id: string, status: ReviewStatus, nowMs: number): Promise<boolean>;
}

export class MemoryStore implements AudienceStore {
  rate = new Map<string, number>();
  phrases = new Map<string, PhraseDoc>();
  pairs = new Map<string, PairDoc>();
  rounds = new Map<string, RoundDoc>();
  votes = new Map<string, Choice>();
  private seq = 0;

  async claimSubmission(uid: string, nowMs: number) {
    const d = decide(this.rate.get(uid), nowMs);
    if (d.ok) this.rate.set(uid, nowMs);
    return d;
  }
  async addPhrase(doc: PhraseDoc) {
    const id = `ph${++this.seq}`;
    this.phrases.set(id, doc);
    return id;
  }
  async addPair(doc: PairDoc) {
    const id = `pa${++this.seq}`;
    this.pairs.set(id, doc);
    return id;
  }
  async getRound(roundId: string) {
    return this.rounds.get(roundId) ?? null;
  }
  async addVote(roundId: string, uid: string, choice: Choice) {
    const key = `${roundId}/${uid}`;
    if (this.votes.has(key)) return false;
    this.votes.set(key, choice);
    return true;
  }
  async listPending(kind: "phrases" | "pairs", event: string) {
    const src = kind === "phrases" ? this.phrases : this.pairs;
    return [...src.entries()]
      .filter(([, d]) => d.status === "pending" && d.event === event)
      .sort(([, a], [, b]) => a.createdAt - b.createdAt)
      .map(([id, d]) => ({ id, ...d }));
  }
  async review(kind: "phrases" | "pairs", id: string, status: ReviewStatus, nowMs: number) {
    const src = (kind === "phrases" ? this.phrases : this.pairs) as Map<string, PhraseDoc | PairDoc>;
    const d = src.get(id);
    if (!d) return false;
    src.set(id, { ...d, status, ...(status === "approved" ? { approvedAt: nowMs } : {}) });
    return true;
  }
}
