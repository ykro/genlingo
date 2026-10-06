// Make an email account a presenter (custom claim admin=true). Creates the account if missing
// with a random password nobody sees: the presenter then uses "Olvidé mi contraseña" on /admin
// to set their own. Pass --password-out=FILE to write the generated password (rehearsal/e2e only).
//   GOOGLE_CLOUD_PROJECT=ai-experiments-487722 node scripts/set-admin.mjs "${ADMIN_EMAILS%%,*}"   # first address of ADMIN_EMAILS (web/.env.local)
import { randomBytes } from "node:crypto";
import { appendFileSync } from "node:fs";

import { initializeApp } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";

const email = process.argv[2];
const out = process.argv.find((a) => a.startsWith("--password-out="))?.split("=")[1];
if (!email) {
  console.error("uso: node scripts/set-admin.mjs <email> [--password-out=.env.local]");
  process.exit(1);
}
initializeApp({ projectId: process.env.GOOGLE_CLOUD_PROJECT ?? "ai-experiments-487722" });
const auth = getAuth();
let user = await auth.getUserByEmail(email).catch(() => null);
if (!user) {
  const password = randomBytes(18).toString("base64url");
  user = await auth.createUser({ email, password, emailVerified: true });
  if (out) appendFileSync(out, `E2E_ADMIN_EMAIL=${email}\nE2E_ADMIN_PASSWORD=${password}\n`);
  console.log(`cuenta creada para ${email}${out ? ` (contraseña en ${out})` : ""}`);
}
await auth.setCustomUserClaims(user.uid, { ...(user.customClaims ?? {}), admin: true });
console.log(`admin=true para ${email} (${user.uid}).`);
