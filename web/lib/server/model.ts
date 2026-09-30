/**
 * Firestore data model of the audience app (database `genlingo`).
 *
 *   phrases/{id}              a phrase sent from a phone; the presenter approves it in /admin
 *   rounds/{id}               a duel on screen, published by the duel service; phones vote on it
 *   rounds/{id}/votes/{uid}   one vote per person (the doc id is the voter's uid)
 *   pairs/{id}                a Gen Z <-> parents pair contributed by the audience (origin=human)
 *   rateLimits/{uid}          last submission times; 20 s between submissions, checked here
 *
 * Every write goes through the API routes (Admin SDK). Security rules deny direct client
 * writes, so the rate limit, validation and blocklist cannot be skipped.
 */

export const COLLECTIONS = {
  phrases: "phrases",
  rounds: "rounds",
  votes: "votes",
  pairs: "pairs",
  rateLimits: "rateLimits",
} as const;

export const DIRECTIONS = ["genz_to_parent", "parent_to_genz"] as const;
export type Direction = (typeof DIRECTIONS)[number];

export const COUNTRIES = ["MX", "GT", "CO", "LATAM"] as const;
export type Country = (typeof COUNTRIES)[number];

export const AGE_RANGES = ["<16", "16-24", "25-34", "35-44", "45-60", "60+"] as const;

export type ReviewStatus = "pending" | "approved" | "rejected";
export type PhraseStatus = ReviewStatus | "shown";
export type Choice = "david" | "goliath";

export interface PhraseDoc {
  text: string;
  direction: Direction;
  country: Country;
  uid: string;
  event: string;
  status: PhraseStatus;
  createdAt: number;
  approvedAt?: number;
  blockedBy?: string;
}

export interface PairDoc {
  source: string;
  target: string;
  direction: Direction;
  country: Country;
  ageRange: string;
  uid: string;
  event: string;
  status: ReviewStatus;
  createdAt: number;
}

export interface RoundDoc {
  event: string;
  phrase: string;
  direction: Direction;
  country: Country;
  david: string;
  goliath: string;
  roundType: "evaluation" | "audience";
  status: "voting" | "closed";
}

/** Seconds between two submissions from the same person (phrases and pairs share it). */
export const RATE_LIMIT_MS = 20_000;
export const MAX_WORDS = 30;
export const MAX_CHARS = 240;
