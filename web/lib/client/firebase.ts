"use client";

import { type FirebaseApp, getApps, initializeApp } from "firebase/app";
import { type Auth, getAuth } from "firebase/auth";
import { type Firestore, getFirestore } from "firebase/firestore";

import type { PublicConfig } from "./config";

let instance: { app: FirebaseApp; auth: Auth; db: Firestore } | null = null;

export function firebase(config: PublicConfig) {
  if (!instance) {
    const app = getApps()[0] ?? initializeApp(config.firebase);
    instance = { app, auth: getAuth(app), db: getFirestore(app, config.database) };
  }
  return instance;
}
