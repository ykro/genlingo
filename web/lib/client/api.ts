"use client";

import { getToken } from "firebase/app-check";
import type { User } from "firebase/auth";

import { currentAppCheck } from "./firebase";

async function appCheckHeader(): Promise<Record<string, string>> {
  const appCheck = currentAppCheck();
  if (!appCheck) return {};
  try {
    return { "X-Firebase-AppCheck": (await getToken(appCheck, false)).token };
  } catch {
    return {}; // the server answers 401 with a clear message if it requires App Check
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string, public retryAfterMs?: number) {
    super(message);
  }
}

/** POST/GET to our API routes with the Firebase ID token. Errors carry the Spanish message. */
export async function api<T = Record<string, unknown>>(user: User, path: string, body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method: body === undefined ? "GET" : "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${await user.getIdToken()}`,
        ...(await appCheckHeader()),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "Sin conexión. Revisa tu internet e intenta de nuevo.");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, data.error ?? "Algo falló. Intenta de nuevo.", data.retryAfterMs);
  return data as T;
}
