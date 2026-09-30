/** GET /api/health — liveness for Cloud Run. */
export function GET() {
  return Response.json({ ok: true, event: process.env.EVENT_ID ?? "ensayo" });
}
