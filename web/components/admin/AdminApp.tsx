"use client";

import { onAuthStateChanged, sendPasswordResetEmail, signInWithEmailAndPassword, signOut, type User } from "firebase/auth";
import { type FormEvent, useCallback, useEffect, useState } from "react";

import { LogoMark, Wordmark } from "@/components/Logo";
import { api, ApiError } from "@/lib/client/api";
import { COUNTRY_LABEL, DIRECTION_LABEL, type PublicConfig, useConfig } from "@/lib/client/config";
import { firebase } from "@/lib/client/firebase";

import s from "./admin.module.css";

type Kind = "phrases" | "pairs";
interface Item {
  id: string;
  text?: string;
  source?: string;
  target?: string;
  direction: keyof typeof DIRECTION_LABEL;
  country: keyof typeof COUNTRY_LABEL;
  ageRange?: string;
  createdAt: number;
}

/**
 * Presenter console (email sign-in): approve audience phrases before they reach the screen,
 * and audience pairs before they become training data. Every action goes through the API,
 * which re-checks that this account is a presenter.
 */
export function AdminApp() {
  const { config, error } = useConfig();
  const [user, setUser] = useState<User | null | undefined>(undefined);

  useEffect(() => {
    if (!config) return;
    return onAuthStateChanged(firebase(config).auth, (u) => setUser(u && !u.isAnonymous ? u : null));
  }, [config]);

  if (error) return <Frame><p className={s.empty} role="alert">No se pudo cargar la configuración. Recarga la página.</p></Frame>;
  if (!config || user === undefined) return <Frame><p className={s.loading} aria-busy="true">Cargando…</p></Frame>;
  if (!user) return <Frame><SignIn config={config} /></Frame>;
  return <Console config={config} user={user} />;
}

function Frame({ children, right }: { children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className={s.page}>
      <header className={s.header}>
        <span className={s.brand}>
          <LogoMark size={28} />
          <Wordmark className={s.wordmark} />
          <span className={`eyebrow ${s.badge}`}>Presentador</span>
        </span>
        {right}
      </header>
      <main className={s.main}>{children}</main>
    </div>
  );
}

function SignIn({ config }: { config: PublicConfig }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const { auth } = firebase(config);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      await signInWithEmailAndPassword(auth, email.trim(), password);
    } catch {
      setMsg({ kind: "error", text: "Correo o contraseña incorrectos." });
    } finally {
      setBusy(false);
    }
  }

  async function reset() {
    if (!email.trim()) return setMsg({ kind: "error", text: "Escribe tu correo para enviarte el enlace." });
    await sendPasswordResetEmail(auth, email.trim()).catch(() => undefined);
    // Same message whether or not the account exists: don't leak who is a presenter.
    setMsg({ kind: "ok", text: "Si la cuenta existe, te llegó un correo para crear una contraseña nueva." });
  }

  return (
    <form className={s.signin} onSubmit={submit}>
      <h1 className={`display ${s.title}`}>Entrar a la consola</h1>
      <p className={s.muted}>Aprueba las frases del público antes de que salgan en pantalla.</p>
      <label className={s.field}>
        <span>Correo</span>
        <input type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </label>
      <label className={s.field}>
        <span>Contraseña</span>
        <input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </label>
      <div className={s.row}>
        <button className={s.primary} disabled={busy}>{busy ? "Entrando…" : "Entrar"}</button>
        <button type="button" className={s.link} onClick={reset}>Olvidé mi contraseña</button>
      </div>
      {msg && <p className={msg.kind === "ok" ? s.ok : s.err} role={msg.kind === "ok" ? "status" : "alert"}>{msg.text}</p>}
    </form>
  );
}

function ago(ms: number) {
  const s = Math.max(0, Math.round((Date.now() - ms) / 1000));
  return s < 60 ? `hace ${s} s` : `hace ${Math.round(s / 60)} min`;
}

function Console({ config, user }: { config: PublicConfig; user: User }) {
  const [kind, setKind] = useState<Kind>("phrases");
  const [items, setItems] = useState<Record<Kind, Item[] | null>>({ phrases: null, pairs: null });
  const [problem, setProblem] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [, tick] = useState(0);
  const [hidden, setHidden] = useState<ReadonlySet<string>>(new Set()); // optimistic: reviewed rows vanish at once

  const load = useCallback(async () => {
    try {
      const [p, q] = await Promise.all([
        api<{ items: Item[] }>(user, "/api/admin/phrases/queue"),
        api<{ items: Item[] }>(user, "/api/admin/pairs/queue"),
      ]);
      setItems({ phrases: p.items, pairs: q.items });
      setProblem(null);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) setForbidden(true);
      else setProblem(e instanceof ApiError ? e.message : "No se pudo actualizar la fila.");
    }
  }, [user]);

  // Poll every 2 s: approvals must reach the stage in under 3 s, and polling survives flaky Wi-Fi.
  useEffect(() => {
    const first = setTimeout(load, 0);
    const t = setInterval(() => {
      load();
      tick((n) => n + 1); // refresh the "hace N s" labels
    }, 2000);
    return () => {
      clearTimeout(first);
      clearInterval(t);
    };
  }, [load]);

  async function review(id: string, action: "approve" | "reject") {
    setHidden((h) => new Set(h).add(id));
    try {
      await api(user, `/api/admin/${kind}/${id}`, { action });
    } catch (e) {
      setHidden((h) => {
        const next = new Set(h);
        next.delete(id);
        return next;
      });
      setProblem(e instanceof ApiError ? e.message : "No se pudo guardar la decisión.");
    }
  }

  const signOutBtn = (
    <button className={s.link} onClick={() => signOut(firebase(config).auth)}>
      Salir ({user.email})
    </button>
  );
  if (forbidden) {
    return (
      <Frame right={signOutBtn}>
        <p className={s.empty} role="alert">Esta cuenta no es de presentador. Pide acceso o entra con otra cuenta.</p>
      </Frame>
    );
  }

  const visible = (k: Kind) => items[k]?.filter((i) => !hidden.has(i.id)) ?? null;
  const list = visible(kind);
  return (
    <Frame right={signOutBtn}>
      <div className={s.toolbar}>
        <div role="tablist" className={s.tabs} aria-label="Filas de revisión">
          {(["phrases", "pairs"] as const).map((k) => (
            <button key={k} role="tab" aria-selected={kind === k} className={kind === k ? s.tabOn : s.tab} onClick={() => setKind(k)}>
              {k === "phrases" ? "Frases para el duelo" : "Pares para entrenar"}
              <span className={`tabular ${s.count}`}>{visible(k)?.length ?? "–"}</span>
            </button>
          ))}
        </div>
        <span className={s.muted}>Evento <b>{config.event}</b> · se actualiza cada 2 s</span>
      </div>
      {problem && <p className={s.err} role="alert">{problem}</p>}
      {list === null ? (
        <ul className={s.list} aria-busy="true">
          {[0, 1, 2].map((i) => <li key={i} className={s.skeletonRow} />)}
        </ul>
      ) : list.length === 0 ? (
        <div className={s.emptyBox}>
          <p className={`display ${s.emptyTitle}`}>{kind === "phrases" ? "Sin frases en la fila" : "Sin pares por revisar"}</p>
          <p className={s.muted}>
            {kind === "phrases"
              ? "Las frases del público llegan aquí después del filtro de lenguaje. Al aprobar una, aparece en la pantalla del duelo en segundos."
              : "Los pares que aporte el público aparecen aquí. Los aprobados se exportan con make export para el próximo entrenamiento."}
          </p>
        </div>
      ) : (
        <ul className={s.list}>
          {list.map((item) => (
            <li key={item.id} className={s.item}>
              <div className={s.itemBody}>
                <span className={`eyebrow ${s.meta}`}>
                  {DIRECTION_LABEL[item.direction]} · {COUNTRY_LABEL[item.country]} · {ago(item.createdAt)}
                  {item.ageRange && item.ageRange !== "unknown" ? ` · ${item.ageRange} años` : ""}
                </span>
                {kind === "phrases" ? (
                  <p className={`display ${s.itemText}`}>{item.text}</p>
                ) : (
                  <p className={s.pair}>
                    <span className={`display ${s.itemText}`}>{item.source}</span>
                    <span aria-hidden className={s.arrow}>→</span>
                    <span className={`display ${s.itemText}`}>{item.target}</span>
                  </p>
                )}
              </div>
              <div className={s.actions}>
                <button className={s.approve} onClick={() => review(item.id, "approve")}>Aprobar</button>
                <button className={s.reject} onClick={() => review(item.id, "reject")}>Rechazar</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Frame>
  );
}
