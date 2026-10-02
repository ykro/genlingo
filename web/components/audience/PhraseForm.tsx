"use client";

import type { User } from "firebase/auth";
import { type FormEvent, useState } from "react";

import { api, ApiError } from "@/lib/client/api";
import { DIRECTION_LABEL } from "@/lib/client/config";

import s from "./audience.module.css";
import { useCooldown } from "./useCooldown";

type Direction = keyof typeof DIRECTION_LABEL;
const WINDOW_MS = 20_000;

/** Send a phrase for the duel. It goes to the presenter's queue, not straight to the screen. */
export function PhraseForm({ user, country }: { user: User; country: string }) {
  const [direction, setDirection] = useState<Direction>("genz_to_parent");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const cooldown = useCooldown();
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim() || busy || cooldown.remainingMs) return;
    setBusy(true);
    setStatus(null);
    try {
      const res = await api<{ status: string; message: string }>(user, "/api/phrases", { text, direction, country });
      setText("");
      cooldown.start(WINDOW_MS);
      setStatus({ kind: "ok", text: res.message });
    } catch (err) {
      const apiErr = err instanceof ApiError ? err : null;
      if (apiErr?.retryAfterMs) cooldown.start(apiErr.retryAfterMs);
      setStatus({ kind: "error", text: apiErr?.message ?? "No se pudo enviar. Intenta de nuevo." });
    } finally {
      setBusy(false);
    }
  }

  const placeholder = direction === "genz_to_parent" ? "no manches, está bien mid" : "qué pena con usted, mijo";
  return (
    <form className={s.form} onSubmit={submit} noValidate>
      <h2 className={`display ${s.formTitle}`}>Reta a los modelos</h2>
      <fieldset className={s.segmented}>
        <legend className="sr-only">Dirección</legend>
        {(Object.keys(DIRECTION_LABEL) as Direction[]).map((d) => (
          <label key={d} className={direction === d ? s.segmentOn : s.segment}>
            <input type="radio" name="direction" value={d} checked={direction === d} onChange={() => setDirection(d)} />
            {DIRECTION_LABEL[d]}
          </label>
        ))}
      </fieldset>
      <label htmlFor="phrase" className="sr-only">
        Tu frase
      </label>
      <div className={s.inputRow}>
        <input
          id="phrase"
          className={s.input}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={placeholder}
          maxLength={240}
          autoComplete="off"
          enterKeyHint="send"
          aria-describedby="phrase-help"
        />
        <button className={s.send} disabled={!text.trim() || busy || cooldown.remainingMs > 0}>
          {cooldown.remainingMs > 0 ? `${cooldown.seconds} s` : busy ? "Enviando…" : "Enviar"}
        </button>
      </div>
      <p id="phrase-help" className={words > 30 ? s.helpError : s.help}>
        {words > 30 ? `Máximo 30 palabras (llevas ${words}).` : "Hasta 30 palabras. Sin nombres, teléfonos ni enlaces."}
      </p>
      {status && (
        <p className={status.kind === "ok" ? s.success : s.error} role={status.kind === "ok" ? "status" : "alert"}>
          {status.text}
        </p>
      )}
    </form>
  );
}
