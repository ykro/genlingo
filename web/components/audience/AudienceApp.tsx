"use client";

import { onAuthStateChanged, signInAnonymously, type User } from "firebase/auth";
import { collection, doc, limit, onSnapshot, orderBy, query, where } from "firebase/firestore";
import { useCallback, useEffect, useState } from "react";

import { LogoMark, Wordmark } from "@/components/Logo";
import { api, ApiError } from "@/lib/client/api";
import { DIRECTION_LABEL, type PublicConfig, useConfig } from "@/lib/client/config";
import { firebase } from "@/lib/client/firebase";

import { PairForm } from "./PairForm";
import { PhraseForm } from "./PhraseForm";
import s from "./audience.module.css";

type Direction = keyof typeof DIRECTION_LABEL;
interface Round {
  id: string;
  phrase: string;
  direction: Direction;
  david: string;
  goliath: string;
  status: "voting" | "closed";
  number?: number;
}

/** The phone app: join by QR (anonymous sign-in, no sign-up), vote each round, send phrases. */
export function AudienceApp() {
  const { config, error, retry } = useConfig();
  const [user, setUser] = useState<User | null>(null);
  const [authError, setAuthError] = useState(false);

  useEffect(() => {
    if (!config) return;
    const { auth } = firebase(config);
    const off = onAuthStateChanged(auth, (u) => {
      if (u) setUser(u);
      else signInAnonymously(auth).catch(() => setAuthError(true));
    });
    return off;
  }, [config]);

  if (error || authError) {
    return (
      <Shell>
        <div className={s.state} role="alert">
          <p className={`display ${s.stateTitle}`}>No pudimos conectarte</p>
          <p className={s.stateText}>Revisa que tengas internet y vuelve a intentarlo.</p>
          <button className={s.secondaryButton} onClick={() => (setAuthError(false), retry())}>
            Reintentar
          </button>
        </div>
      </Shell>
    );
  }
  if (!config || !user) {
    return (
      <Shell>
        <div className={s.state} aria-busy="true" aria-live="polite">
          <span className={s.loader} aria-hidden />
          <p className={s.stateText}>Entrando al duelo…</p>
        </div>
      </Shell>
    );
  }
  return <Joined config={config} user={user} />;
}

function Shell({ children, roundLabel }: { children: React.ReactNode; roundLabel?: string }) {
  return (
    <div className={s.page}>
      <header className={s.header}>
        <span className={s.brand}>
          <LogoMark size={30} />
          <Wordmark className={s.wordmark} />
        </span>
        {roundLabel && <span className={`display ${s.roundLabel}`}>{roundLabel}</span>}
      </header>
      <main className={s.main}>{children}</main>
    </div>
  );
}

function Joined({ config, user }: { config: PublicConfig; user: User }) {
  const [round, setRound] = useState<Round | null | undefined>(undefined);
  const [vote, setVote] = useState<{ roundId: string; choice: "david" | "goliath" } | null>(null);

  // The round on screen, in real time (published by the duel service on the stage laptop).
  useEffect(() => {
    const { db } = firebase(config);
    const q = query(collection(db, "rounds"), where("event", "==", config.event), orderBy("createdAt", "desc"), limit(1));
    return onSnapshot(
      q,
      (snap) => setRound(snap.empty ? null : ({ id: snap.docs[0].id, ...snap.docs[0].data() } as Round)),
      () => setRound(null),
    );
  }, [config]);

  // Did I already vote in this round? (rules let me read only my own vote)
  const roundId = round?.id;
  useEffect(() => {
    if (!roundId) return;
    const { db } = firebase(config);
    return onSnapshot(
      doc(db, "rounds", roundId, "votes", user.uid),
      (snap) => snap.exists() && setVote({ roundId, choice: snap.data().choice }),
      () => undefined,
    );
  }, [config, roundId, user.uid]);
  // A vote only counts for the round it was cast in.
  const myVote = vote && vote.roundId === roundId ? vote.choice : null;

  return (
    <Shell roundLabel={round?.number ? `Ronda ${round.number}` : undefined}>
      <RoundCard round={round} user={user} myVote={myVote} onVoted={(choice) => roundId && setVote({ roundId, choice })} />
      <hr className={s.rule} />
      <PhraseForm user={user} country={config.country} />
      <PairForm user={user} country={config.country} />
      <p className={s.footnote}>Una frase cada 20 segundos · Tu voto es anónimo</p>
    </Shell>
  );
}

function RoundCard({
  round,
  user,
  myVote,
  onVoted,
}: {
  round: Round | null | undefined;
  user: User;
  myVote: "david" | "goliath" | null;
  onVoted: (c: "david" | "goliath") => void;
}) {
  const [pending, setPending] = useState<"david" | "goliath" | null>(null);
  const [failure, setFailure] = useState<{ roundId: string; text: string } | null>(null);
  const error = failure && failure.roundId === round?.id ? failure.text : null;
  const setError = (text: string | null) => setFailure(text && round ? { roundId: round.id, text } : null);

  const vote = useCallback(
    async (choice: "david" | "goliath") => {
      if (!round) return;
      setPending(choice);
      setError(null);
      try {
        await api(user, "/api/votes", { roundId: round.id, choice });
        onVoted(choice); // the snapshot confirms it a moment later
      } catch (e) {
        setError(e instanceof ApiError ? e.message : "No se pudo registrar tu voto.");
      } finally {
        setPending(null);
      }
    },
    [round, user, onVoted], // eslint-disable-line react-hooks/exhaustive-deps
  );

  if (round === undefined) {
    return (
      <section className={s.round} aria-busy="true">
        <span className={`${s.skeleton} ${s.skeletonEyebrow}`} />
        <span className={`${s.skeleton} ${s.skeletonLine}`} />
        <span className={`${s.skeleton} ${s.skeletonLineShort}`} />
      </section>
    );
  }
  if (round === null) {
    return (
      <section className={s.round}>
        <p className="eyebrow">Antes del duelo</p>
        <h1 className={`display ${s.phrase}`}>El duelo está por empezar.</h1>
        <p className={s.lead}>
          Cuando aparezca una frase en la pantalla, aquí votas quién la tradujo mejor: <b className={s.davidText}>David</b>, el
          modelo pequeño en la laptop, o <b className={s.goliathText}>Goliath</b>, el gigante en la nube.
        </p>
      </section>
    );
  }

  const closed = round.status !== "voting";
  return (
    <section className={s.round} aria-live="polite">
      <p className="eyebrow">{DIRECTION_LABEL[round.direction]}</p>
      <h1 className={`display ${s.phrase}`}>{round.phrase}</h1>
      <div className={s.votes} role="group" aria-label="Votar">
        {(["david", "goliath"] as const).map((side) => {
          const chosen = myVote === side;
          return (
            <button
              key={side}
              className={`${s.vote} ${s[side]} ${chosen ? s.chosen : ""} ${(myVote || closed) && !chosen ? s.notChosen : ""}`}
              disabled={closed || !!myVote || !!pending}
              aria-pressed={chosen}
              onClick={() => vote(side)}
            >
              <span className={`display ${s.voteLabel}`}>
                {chosen ? "✓ Votaste por " : pending === side ? "Votando por " : "Votar por "}
                {side === "david" ? "David" : "Goliath"}
              </span>
              <span className={s.voteText}>{side === "david" ? round.david : round.goliath}</span>
            </button>
          );
        })}
      </div>
      {error && (
        <p className={s.error} role="alert">
          {error}
        </p>
      )}
      {closed && !myVote && <p className={s.note}>La votación de esta ronda ya cerró. Espera la siguiente frase.</p>}
      {myVote && <p className={s.note}>Tu voto ya cuenta. Mira el marcador en la pantalla.</p>}
    </section>
  );
}
