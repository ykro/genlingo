import { connection } from "next/server";

/**
 * GET /api/config — public runtime configuration for the browser (read from env at request
 * time, so one image serves every event). The Firebase web config is public by design;
 * security comes from Auth, the API routes and the Firestore rules.
 */
export async function GET() {
  await connection();
  return Response.json({
    firebase: {
      apiKey: process.env.FIREBASE_API_KEY ?? "",
      authDomain: process.env.FIREBASE_AUTH_DOMAIN ?? "",
      projectId: process.env.GOOGLE_CLOUD_PROJECT ?? "",
      appId: process.env.FIREBASE_APP_ID ?? "",
    },
    database: process.env.FIRESTORE_DATABASE ?? "genlingo",
    event: process.env.EVENT_ID ?? "ensayo",
    country: process.env.EVENT_COUNTRY ?? "LATAM",
    audienceUrl: process.env.AUDIENCE_URL ?? "",
    duelUrl: process.env.DUEL_URL ?? "http://127.0.0.1:8787",
  });
}
