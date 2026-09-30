import "server-only";

import { getApps, initializeApp } from "firebase-admin/app";
import { getAppCheck } from "firebase-admin/app-check";
import { getAuth } from "firebase-admin/auth";
import { getFirestore } from "firebase-admin/firestore";

import { FirestoreStore } from "./firestore-store";

// ADC on Cloud Run (the service account) and locally (gcloud auth application-default login).
const app = getApps()[0] ?? initializeApp({ projectId: process.env.GOOGLE_CLOUD_PROJECT });

export const adminAuth = getAuth(app);
export const appCheck = getAppCheck(app);
export const db = getFirestore(app, process.env.FIRESTORE_DATABASE ?? "genlingo");
export const store = new FirestoreStore(db);
