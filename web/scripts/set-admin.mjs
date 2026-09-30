// Give the presenter's email account the `admin` custom claim (reads the review queues in
// the rules; the API also accepts ADMIN_EMAILS). The account must exist (email sign-in).
//   GOOGLE_CLOUD_PROJECT=ai-experiments-487722 node scripts/set-admin.mjs presenter@example.com
import { initializeApp } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";

const email = process.argv[2];
if (!email) {
  console.error("uso: node scripts/set-admin.mjs <email>");
  process.exit(1);
}
initializeApp({ projectId: process.env.GOOGLE_CLOUD_PROJECT ?? "ai-experiments-487722" });
const user = await getAuth().getUserByEmail(email);
await getAuth().setCustomUserClaims(user.uid, { ...(user.customClaims ?? {}), admin: true });
console.log(`admin=true para ${email} (${user.uid}). Cierra y abre sesión para refrescar el token.`);
