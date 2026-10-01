"use client";

import type { User } from "firebase/auth";
import { type FormEvent, useState } from "react";

import { api, ApiError } from "@/lib/client/api";
import { COUNTRY_LABEL, DIRECTION_LABEL, type PublicConfig } from "@/lib/client/config";

import s from "./audience.module.css";
import { useCooldown } from "./useCooldown";

type Direction = keyof typeof DIRECTION_LABEL;
const AGES = ["<16", "16-24", "25-34", "35-44", "45-60", "60+"] as const;

/**
 * "Teach David": contribute a pair. Approved pairs become origin=human training data for next
 * month's David. Collapsed by default: voting and phrases come first.
 */
export function PairForm({ user, country }: { user: User; country: PublicConfig["country"] }) {
  const [open, setOpen] = useState(false);
  const [direction, setDirection] = useState<Direction>("genz_to_parent");
  const [source, setSource] = useState("");
  const [target, setTarget] = useState("");
  const [ageRange, setAgeRange] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const cooldown = useCooldown();

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (busy || cooldown.remainingMs) return;
    setBusy(true);
    setStatus(null);
    try {
      await api(user, "/api/pairs", { source, target, direction, country, ageRange });
      setSource("");
      setTarget("");
      cooldown.start(20_000);
      setStatus({ kind: "ok", text: "¡Gracias! Si se aprueba, entrena al David del próximo mes." });
    } catch (err) {
      const apiErr = err instanceof ApiError ? err : null;
      if (apiErr?.retryAfterMs) cooldown.start(apiErr.retryAfterMs);
      setStatus({ kind: "error", text: apiErr?.message ?? "No se pudo enviar. Intenta de nuevo." });
    } finally {
      setBusy(false);
    }
  }

  const [from, to] = direction === "genz_to_parent" ? ["Gen Z", "papás"] : ["papás", "Gen Z"];
  return (
    <section className={s.teach}>
      <button className={s.disclosure} aria-expanded={open} aria-controls="teach-form" onClick={() => setOpen((o) => !o)}>
        <span className="display">Enséñale a David</span>
        <span aria-hidden className={s.chevron}>
          {open ? "−" : "+"}
        </span>
      </button>
      <div id="teach-form" className={s.collapse} data-open={open}>
        <form className={s.form} onSubmit={submit} noValidate inert={!open}>
          <p className={s.help}>
            Escribe una frase y cómo la diría la otra generación en {COUNTRY_LABEL[country]}. Así se arma el set de entrenamiento.
          </p>
          <fieldset className={s.segmented}>
            <legend className="sr-only">Dirección del par</legend>
            {(Object.keys(DIRECTION_LABEL) as Direction[]).map((d) => (
              <label key={d} className={direction === d ? s.segmentOn : s.segment}>
                <input type="radio" name="pair-direction" value={d} checked={direction === d} onChange={() => setDirection(d)} />
                {DIRECTION_LABEL[d]}
              </label>
            ))}
          </fieldset>
          <label className={s.field}>
            <span className={s.fieldLabel}>Cómo lo dice {from}</span>
            <input className={s.input} value={source} onChange={(e) => setSource(e.target.value)} maxLength={240} required />
          </label>
          <label className={s.field}>
            <span className={s.fieldLabel}>Cómo lo dirían {to}</span>
            <input className={s.input} value={target} onChange={(e) => setTarget(e.target.value)} maxLength={240} required />
          </label>
          <label className={s.field}>
            <span className={s.fieldLabel}>Tu edad (opcional)</span>
            <select className={s.input} value={ageRange} onChange={(e) => setAgeRange(e.target.value)}>
              <option value="">Prefiero no decir</option>
              {AGES.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </label>
          <button className={s.secondaryButton} disabled={busy || !source.trim() || !target.trim() || cooldown.remainingMs > 0}>
            {cooldown.remainingMs > 0 ? `Espera ${cooldown.seconds} s` : busy ? "Enviando…" : "Enviar par"}
          </button>
          {status && (
            <p className={status.kind === "ok" ? s.success : s.error} role={status.kind === "ok" ? "status" : "alert"}>
              {status.text}
            </p>
          )}
        </form>
      </div>
    </section>
  );
}
