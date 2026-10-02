import "server-only";

import type { Result } from "./audience";
import { AuthError } from "./auth";
import { ValidationError } from "./validation";

export const EVENT_ID = () => process.env.EVENT_ID ?? "ensayo";

export async function readJson(req: Request): Promise<Record<string, unknown>> {
  try {
    const body = await req.json();
    return body && typeof body === "object" ? body : {};
  } catch {
    return {};
  }
}

export async function respond(fn: () => Promise<Result>): Promise<Response> {
  try {
    const { status, body } = await fn();
    return Response.json(body, { status });
  } catch (err) {
    if (err instanceof AuthError) return Response.json({ error: err.message }, { status: err.status });
    if (err instanceof ValidationError) return Response.json({ error: err.message }, { status: 400 });
    console.error(err);
    return Response.json({ error: "Algo falló de nuestro lado. Intenta de nuevo." }, { status: 500 });
  }
}
