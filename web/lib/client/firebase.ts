"use client";

import { type FirebaseApp, getApps, initializeApp } from "firebase/app";
import { type AppCheck, initializeAppCheck, ReCaptchaEnterpriseProvider } from "firebase/app-check";
import { type Auth, getAuth } from "firebase/auth";
import { type Firestore, getFirestore } from "firebase/firestore";

import type { PublicConfig } from "./config";

const DEBUG_KEY = "genlingo.appcheckDebug";

let instance: { app: FirebaseApp; auth: Auth; db: Firestore; appCheck: AppCheck | null } | null = null;

/**
 * Debug token for automated tests and emulators, which can't pass reCAPTCHA. It comes from the
 * URL once (`#appcheck-debug=<token>`), is kept in this browser, and only works because the
 * same token was registered in App Check (infra/06-app-check.sh). Real phones never have one.
 */
function debugToken(): string | null {
  try {
    const m = location.hash.match(/appcheck-debug=([\w-]+)/);
    if (m) {
      localStorage.setItem(DEBUG_KEY, m[1]);
      history.replaceState(null, "", location.pathname + location.search);
    }
    return localStorage.getItem(DEBUG_KEY);
  } catch {
    return null;
  }
}

export function firebase(config: PublicConfig) {
  if (!instance) {
    const app = getApps()[0] ?? initializeApp(config.firebase);
    let appCheck: AppCheck | null = null;
    if (config.recaptchaSiteKey) {
      // App Check: every Firestore read and every API call proves it comes from this web app.
      const token = debugToken();
      if (token) (self as unknown as { FIREBASE_APPCHECK_DEBUG_TOKEN: string }).FIREBASE_APPCHECK_DEBUG_TOKEN = token;
      appCheck = initializeAppCheck(app, {
        provider: new ReCaptchaEnterpriseProvider(config.recaptchaSiteKey),
        isTokenAutoRefreshEnabled: true,
      });
    }
    instance = { app, auth: getAuth(app), db: getFirestore(app, config.database), appCheck };
  }
  return instance;
}

/** The App Check instance, once firebase() has run (null when App Check is not configured). */
export function currentAppCheck(): AppCheck | null {
  return instance?.appCheck ?? null;
}
