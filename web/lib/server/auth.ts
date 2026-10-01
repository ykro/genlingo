import "server-only";

import { adminAuth, appCheck } from "./firebase-admin";

export class AuthError extends Error {
  constructor(public status: 401 | 403, message: string) {
    super(message);
  }
}

/**
 * Every audience request carries a Firebase ID token (anonymous sign-in: no sign-up, but each
 * phone gets a stable uid, which is what the rate limit and "one vote per person" key on).
 * With App Check enforced, requests must also come from our registered web app.
 */
export async function requireUser(req: Request) {
  if (process.env.APP_CHECK_ENFORCE === "1") {
    const token = req.headers.get("x-firebase-appcheck");
    if (!token) throw new AuthError(401, "Falta la verificación de la app.");
    await appCheck.verifyToken(token).catch(() => {
      throw new AuthError(401, "Verificación de la app inválida.");
    });
  }
  const header = req.headers.get("authorization") ?? "";
  const idToken = header.startsWith("Bearer ") ? header.slice(7) : "";
  if (!idToken) throw new AuthError(401, "Inicia sesión para participar.");
  try {
    return await adminAuth.verifyIdToken(idToken);
  } catch {
    throw new AuthError(401, "Tu sesión expiró. Recarga la página.");
  }
}

/** The presenter signs in with email; admins carry the admin=true claim (scripts/set-admin.mjs)
 * or are listed in ADMIN_EMAILS with a verified email. */
export async function requireAdmin(req: Request) {
  const user = await requireUser(req);
  const admins = (process.env.ADMIN_EMAILS ?? "").split(",").map((e) => e.trim().toLowerCase()).filter(Boolean);
  // ADMIN_EMAILS only counts for verified emails: anyone can sign up with someone else's address.
  const listed = !!user.email && user.email_verified === true && admins.includes(user.email.toLowerCase());
  const isAdmin = user.admin === true || listed;
  if (!isAdmin) throw new AuthError(403, "Solo el presentador puede hacer esto.");
  return user;
}
