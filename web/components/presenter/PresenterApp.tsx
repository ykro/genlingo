"use client";

import QRCode from "qrcode";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import { LogoMark, Wordmark } from "@/components/Logo";
import { type PublicConfig, useConfig } from "@/lib/client/config";

import {
  type ContenderResult,
  type Direction,
  DuelClient,
  type Health,
  type QueuedPhrase,
  type Round,
  type Scoreboard,
  type Side,
} from "./duelClient";
import s from "./presenter.module.css";

const DIRECTION = { genz_to_parent: "Gen Z → papás", parent_to_genz: "Papás → Gen Z" } as const;
const NAME: Record<Side, string> = { david: "David", goliath: "Goliath" };

// ---- formatting --------------------------------------------------------------------------------
const seconds = (ms: number | null | undefined) =>
  ms == null ? "—" : ms < 1000 ? `${(ms / 1000).toFixed(2)} s` : `${(ms / 1000).toFixed(1)} s`;
function usd(x: number | null | undefined) {
  if (x == null) return "—";
  if (x === 0) return "$0";
  if (x >= 0.1) return `$${x.toFixed(2)}`;
  if (x >= 0.01) return `$${x.toFixed(3)}`;
  return `$${x.toPrecision(2)}`;
}
const chrf = (x: number | null | undefined) => (x == null ? "—" : x.toFixed(1));

/** Fixed 1920×1080 stage scaled to the window: the layout is identical on any projector. */
function useStageScale() {
  const [k, setK] = useState(1);
  useLayoutEffect(() => {
    const fit = () => setK(Math.min(window.innerWidth / 1920, window.innerHeight / 1080));
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);
  return k;
}

/** A figure that rolls in when it changes (240 ms, ease-out-quart). */
function Roll({ value, className }: { value: string | number; className?: string }) {
  return (
    <span className={`${s.roll} ${className ?? ""}`}>
      <span key={String(value)} className={s.rollInner}>
        {value}
      </span>
    </span>
  );
}

function Qr({ url, size }: { url: string; size: number }) {
  const [svg, setSvg] = useState("");
  useEffect(() => {
    if (!url) return;
    QRCode.toString(url, { type: "svg", margin: 0, color: { dark: "#16181D", light: "#FFFDF8" }, errorCorrectionLevel: "M" })
      .then(setSvg)
      .catch(() => setSvg(""));
  }, [url]);
  if (!svg) return null;
  return <span className={s.qr} style={{ width: size, height: size }} role="img" aria-label={`Código QR para ${url}`} dangerouslySetInnerHTML={{ __html: svg }} />;
}

// ---- app ---------------------------------------------------------------------------------------
export function PresenterApp() {
  const { config, error } = useConfig();
  const k = useStageScale();
  return (
    <div className={s.viewport}>
      <div className={s.stage} style={{ transform: `translate(-50%, -50%) scale(${k})` }}>
        {error ? (
          <Fatal title="No se pudo cargar la configuración" hint="Revisa que la app web esté corriendo (make up)." />
        ) : config ? (
          <Duel config={config} />
        ) : (
          <div className={s.boot}><LogoMark size={120} /></div>
        )}
      </div>
    </div>
  );
}

function Fatal({ title, hint, onRetry }: { title: string; hint: string; onRetry?: () => void }) {
  return (
    <div className={s.fatal} role="alert">
      <LogoMark size={96} />
      <p className={`display ${s.fatalTitle}`}>{title}</p>
      <p className={s.fatalHint}>{hint}</p>
      {onRetry && <button className={s.fatalButton} onClick={onRetry}>Reintentar</button>}
    </div>
  );
}

function Duel({ config }: { config: PublicConfig }) {
  const client = useMemo(() => new DuelClient(config.duelUrl), [config.duelUrl]);
  const [health, setHealth] = useState<Health | null>(null);
  const [down, setDown] = useState(false);
  const [board, setBoard] = useState<Scoreboard | null>(null);
  const [round, setRound] = useState<Round | null>(null);
  const [queue, setQueue] = useState<QueuedPhrase[]>([]);
  const [liveVotes, setLiveVotes] = useState<{ roundId: string; david: number; goliath: number } | null>(null);
  const [running, setRunning] = useState<{ phrase: string; direction: Direction; startedAt: number } | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [composer, setComposer] = useState(false);
  // "Last month vs this month": M switches which David duels (tags from the duel service).
  const [tagIndex, setTagIndex] = useState(0);
  const davidTags = health?.david_tags?.length ? health.david_tags : health?.david_tag ? [health.david_tag] : [];
  const activeTag = davidTags[tagIndex % Math.max(1, davidTags.length)];

  const refreshBoard = useCallback(
    () => client.scoreboard(activeTag).then(setBoard).catch(() => undefined),
    [client, activeTag],
  );

  // Initial state + health (every 3 s: the offline indicator must react to Wi-Fi going away).
  useEffect(() => {
    let alive = true;
    const tick = () =>
      client
        .health()
        .then((h) => alive && (setHealth(h), setDown(false)))
        .catch(() => alive && setDown(true));
    tick();
    client.latest().then((r) => alive && setRound(r)).catch(() => undefined);
    refreshBoard();
    const t = setInterval(tick, 3000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, [client, refreshBoard]);

  // Approved audience phrases: poll every second (approval -> screen well under 3 s).
  useEffect(() => {
    const t = setInterval(() => client.queue().then(setQueue).catch(() => undefined), 1000);
    return () => clearInterval(t);
  }, [client]);

  // Live votes while an audience round is open.
  // Votes only exist when the audience app is connected; the talk works without any audience.
  const audience = health?.audience_feed ?? false;
  const voting = audience && round?.round_type === "audience" && round.win_reason === null;
  useEffect(() => {
    if (!round || !voting) return;
    const t = setInterval(() => client.votes(round.id).then((v) => setLiveVotes({ roundId: round.id, ...v })).catch(() => undefined), 1500);
    return () => clearInterval(t);
  }, [client, round, voting]);
  const votes = round
    ? voting && liveVotes?.roundId === round.id
      ? liveVotes
      : { david: round.votes_david, goliath: round.votes_goliath }
    : null;

  const run = useCallback(
    async (label: { phrase: string; direction: Direction }, call: () => Promise<Round>) => {
      if (running) return;
      setProblem(null);
      setRunning({ ...label, startedAt: performance.now() });
      try {
        const r = await call();
        setRound(r);
        refreshBoard();
      } catch (e) {
        setProblem(e instanceof Error ? e.message : "El duelo falló.");
      } finally {
        setRunning(null);
      }
    },
    [running, refreshBoard],
  );

  const nextFromAudience = useCallback(() => {
    const next = queue[0];
    if (!next) return setProblem("No hay frases aprobadas en la fila.");
    setQueue((q) => q.slice(1));
    run({ phrase: next.text, direction: next.direction }, () =>
      client.duel({ phrase: next.text, direction: next.direction, country: next.country, phrase_id: next.phrase_id, david_tag: activeTag }),
    );
  }, [queue, run, client, activeTag]);

  const evaluation = useCallback(
    (specialty = false) =>
      run({ phrase: specialty ? "Frase chapín del set de prueba…" : "Frase del set de prueba…", direction: "genz_to_parent" }, () =>
        client.evaluation(activeTag, specialty),
      ),
    [run, client, activeTag],
  );

  const closeVotes = useCallback(async () => {
    if (!round || !voting) return;
    try {
      setRound(await client.close(round.id));
      refreshBoard();
    } catch (e) {
      setProblem(e instanceof Error ? e.message : "No se pudieron cerrar los votos.");
    }
  }, [client, round, voting, refreshBoard]);

  // Keyboard: the presenter drives the show from a clicker or the laptop keyboard.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (composer || e.metaKey || e.ctrlKey || e.altKey) return;
      const key = e.key.toLowerCase();
      if (key === "e") evaluation();
      else if (key === "g") evaluation(true); // specialty round: GT test pairs, fixed seeded order
      else if (key === "enter" || key === "n" || key === "pagedown") nextFromAudience();
      else if (key === "v") closeVotes();
      else if (key === "/") {
        e.preventDefault();
        setComposer(true);
      }
      else if (key === "f") document.documentElement.requestFullscreen?.().catch(() => undefined);
      else if (key === "m" && davidTags.length > 1) setTagIndex((i) => (i + 1) % davidTags.length);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [composer, evaluation, nextFromAudience, closeVotes, davidTags.length]);

  if (down && !health) {
    return (
      <Fatal
        title="El servicio del duelo no responde"
        hint={`Arráncalo en la laptop con make up (${config.duelUrl}).`}
        onRetry={() => client.health().then((h) => (setHealth(h), setDown(false))).catch(() => undefined)}
      />
    );
  }

  const online = health?.online ?? true;
  const davidTag = round?.david_tag && !running ? round.david_tag : activeTag ?? "";
  const previous = davidTags.length > 1 && activeTag !== davidTags[0];
  const model = health?.david_models?.[davidTag];
  const modelNote = model?.quant
    ? `${model.quant}${model.size_bytes ? ` · ${(model.size_bytes / 1e9).toFixed(1)} GB` : ""}`
    : null;
  return (
    <div className={s.layout}>
      <header className={s.top}>
        <span className={s.brand}>
          <LogoMark size={44} />
          <Wordmark className={s.wordmark} />
        </span>
        <span className={s.chips}>
          {queue.length > 0 && (
            <span className={`${s.chip} ${s.queueChip}`} aria-live="polite">
              <b className="tabular">{queue.length}</b> {queue.length === 1 ? "frase del público" : "frases del público"} en fila
            </span>
          )}
          <span className={`${s.chip} ${previous ? s.previousChip : ""}`}>
            David · <b>{davidTag || "sin modelo"}</b>
            {modelNote && <span className={`${s.chipNote} tabular`}>{modelNote}</span>}
            {previous && <span className={s.chipNote}>el del mes pasado</span>}
          </span>
          <span className={`${s.chip} ${online ? s.online : s.offline}`} aria-live="polite">
            <span className={s.dot} aria-hidden />
            {down ? "Duelo sin respuesta" : online ? "En línea" : "Sin conexión"}
          </span>
        </span>
      </header>

      {running ? (
        <RoundView live={running} />
      ) : round ? (
        <RoundView round={round} online={online} />
      ) : (
        <Welcome audienceUrl={config.audienceUrl} />
      )}

      <ScoreBand board={board} round={round} votes={votes} voting={voting} audience={audience} audienceUrl={config.audienceUrl} />

      <ControlBar
        canSwitch={davidTags.length > 1}
        queue={queue}
        problem={problem}
        voting={voting}
        composer={composer}
        onCloseComposer={() => setComposer(false)}
        onCompose={(phrase, direction) => {
          setComposer(false);
          run({ phrase, direction }, () => client.duel({ phrase, direction, country: config.country, david_tag: activeTag }));
        }}
      />
    </div>
  );
}

function Welcome({ audienceUrl }: { audienceUrl: string }) {
  return (
    <section className={s.welcome}>
      <div className={s.welcomeText}>
        <p className={`eyebrow ${s.eyebrow}`}>David contra Goliath</p>
        <h1 className={`display ${s.welcomeTitle}`}>
          Un modelo pequeño en esta laptop contra un gigante en la nube.
        </h1>
        <p className={s.welcomeLead}>Escanea el código, manda una frase de tu generación y vota quién la traduce mejor.</p>
      </div>
      {audienceUrl ? (
        <div className={s.welcomeQr}>
          <Qr url={audienceUrl} size={360} />
          <span className={s.qrUrl}>{audienceUrl.replace(/^https?:\/\//, "")}</span>
        </div>
      ) : null}
    </section>
  );
}

function phraseSize(text: string) {
  const n = text.length;
  return n <= 42 ? 104 : n <= 70 ? 88 : n <= 110 ? 72 : 60;
}
function answerSize(text: string) {
  const n = text.length;
  return n <= 40 ? 88 : n <= 70 ? 72 : n <= 110 ? 58 : 48;
}

/**
 * A translation must always be readable in full from the back of the room: start at the size
 * picked from its length and shrink until it fits its column (no ellipsis, no hidden words).
 */
function FitText({ text, start, min = 36, className }: { text: string; start: number; min?: number; className: string }) {
  const ref = useRef<HTMLParagraphElement>(null);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    let size = start;
    el.style.fontSize = `${size}px`;
    // Display glyphs poke a little above/below a tight line box; only a hidden line counts as overflow.
    while (size > min && el.scrollHeight - el.clientHeight > size * 0.4) {
      size -= 4;
      el.style.fontSize = `${size}px`;
    }
  }, [text, start, min]);
  return (
    <p ref={ref} className={className} style={{ fontSize: start }}>
      {text}
    </p>
  );
}

function RoundView({ round, live, online = true }: { round?: Round; live?: { phrase: string; direction: Direction; startedAt: number }; online?: boolean }) {
  const phrase = round?.phrase ?? live!.phrase;
  const direction = round?.direction ?? live!.direction;
  const eyebrow = [
    round?.number ? `Ronda ${round.number}` : live ? "Nueva ronda" : null,
    DIRECTION[direction],
    round ? (round.label ?? (round.round_type === "evaluation" ? "Set de prueba" : round.phrase_id ? "Frase del público" : "Frase en vivo")) : null,
  ]
    .filter(Boolean)
    .join(" · ");
  return (
    <section className={s.round} aria-live="polite">
      <p className={`eyebrow ${s.eyebrow}`}>{eyebrow}</p>
      <h1 className={`display ${s.phrase}`} style={{ fontSize: phraseSize(phrase) }}>
        {phrase}
      </h1>
      {round?.reference && (
        <p className={s.reference}>
          <span className="eyebrow">Referencia humana</span> {round.reference}
        </p>
      )}
      <div className={s.columns}>
        {(["david", "goliath"] as const).map((side) => (
          <Column
            key={side}
            side={side}
            result={round?.[side]}
            startedAt={live?.startedAt}
            winner={round?.winner === side}
            loser={!!round?.winner && round.winner !== "draw" && round.winner !== side}
            evaluation={round?.round_type === "evaluation"}
            online={online}
          />
        ))}
      </div>
    </section>
  );
}

function Stopwatch({ startedAt }: { startedAt: number }) {
  const [now, setNow] = useState(() => performance.now());
  useEffect(() => {
    let raf = 0;
    const loop = () => ((raf = requestAnimationFrame(loop)), setNow(performance.now()));
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);
  return <span className="tabular">{seconds(now - startedAt)}</span>;
}

function Column({
  side,
  result,
  startedAt,
  winner,
  loser,
  evaluation,
  online,
}: {
  side: Side;
  result?: ContenderResult;
  startedAt?: number;
  winner: boolean;
  loser: boolean;
  evaluation: boolean;
  online: boolean;
}) {
  const label = (
    <h2 className={`display ${s.side} ${s[side]}`}>
      <span className={winner ? s.winner : undefined}>{NAME[side]}</span>
      <span className={s.sideMeta}>{side === "david" ? "en esta laptop" : "en la nube"}</span>
    </h2>
  );
  if (!result) {
    return (
      <article className={s.column} aria-busy="true">
        {label}
        <p className={`display ${s.thinking}`}>
          {side === "goliath" && !online ? "Sin conexión" : "Traduciendo"}
          <span className={s.ellipsis} aria-hidden />
        </p>
        <p className={`display ${s.figure}`}>{startedAt != null && <Stopwatch startedAt={startedAt} />}</p>
      </article>
    );
  }
  if (result.status !== "ok") {
    return (
      <article className={`${s.column} ${s.out}`}>
        {label}
        <p className={`display ${s.outTitle}`}>{result.status === "offline" ? "Sin conexión" : "No respondió"}</p>
        <p className={s.outText}>
          {result.status === "offline"
            ? side === "goliath"
              ? "Goliath vive en la nube y necesita internet. David sigue funcionando en la laptop."
              : "David no está cargado en Ollama."
            : "La llamada falló o tardó demasiado; la ronda sigue sin él."}
        </p>
      </article>
    );
  }
  return (
    <article className={`${s.column} ${loser ? s.loser : ""}`}>
      {label}
      <FitText className={`display ${s.answer}`} text={result.text} start={answerSize(result.text)} />
      {!!result.extra?.glossary?.length && (
        // Retrieval over our own term bank: shown, because it's part of why David answers well.
        <p className={s.glossary}>
          <span className="eyebrow">Glosario</span> {result.extra.glossary.join(" · ")}
        </p>
      )}
      <dl className={s.stats}>
        <div>
          <dt className="eyebrow">Latencia</dt>
          <dd className={`display tabular ${s.figure}`}>{seconds(result.latency_ms)}</dd>
        </div>
        <div>
          <dt className="eyebrow">Costo</dt>
          <dd className={`display tabular ${s.figure}`}>{usd(result.cost_usd)}</dd>
        </div>
        {evaluation && (
          <div>
            <dt className="eyebrow">chrF++</dt>
            <dd className={`display tabular ${s.figure}`}>{chrf(result.chrf)}</dd>
          </div>
        )}
      </dl>
    </article>
  );
}

function ScoreBand({
  board,
  round,
  votes,
  voting,
  audience,
  audienceUrl,
}: {
  board: Scoreboard | null;
  round: Round | null;
  votes: { david: number; goliath: number } | null;
  voting: boolean;
  audience: boolean;
  audienceUrl: string;
}) {
  const training = board?.david_training?.estimated_cost_usd ?? null;
  const perRound = training != null && board?.rounds ? training / board.rounds : null;
  const total = votes ? votes.david + votes.goliath : 0;
  const pct = total ? Math.round((votes!.david / total) * 100) : 50;
  const showVotes = audience && round?.round_type === "audience";
  return (
    <section className={s.band} aria-label="Marcador">
      <div className={s.wins}>
        <Roll value={board?.david.wins ?? 0} className={`${s.bigScore} ${s.davidText}`} />
        <span className={s.winsRule} aria-hidden />
        <Roll value={board?.goliath.wins ?? 0} className={`${s.bigScore} ${s.goliathText}`} />
      </div>
      <table className={s.stat}>
        <thead>
          <tr>
            <th scope="col"><span className="sr-only">Modelo</span></th>
            <th scope="col" className="eyebrow">chrF++ medio</th>
            <th scope="col" className="eyebrow">Latencia p50</th>
            <th scope="col" className="eyebrow">Costo acumulado</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row" className={`display ${s.davidText}`}>David</th>
            <td className="tabular"><Roll value={chrf(board?.david.avg_chrf)} /></td>
            <td className="tabular"><Roll value={seconds(board?.david.p50_latency_ms)} /></td>
            <td className="tabular">
              <Roll value={usd(board?.david.cost_usd ?? 0)} />
              {training != null && (
                <span className={s.amortized}>
                  entrenar: {usd(training)}
                  {perRound != null ? ` · ${usd(perRound)}/ronda` : ""}
                </span>
              )}
            </td>
          </tr>
          <tr>
            <th scope="row" className={`display ${s.goliathText}`}>Goliath</th>
            <td className="tabular"><Roll value={chrf(board?.goliath.avg_chrf)} /></td>
            <td className="tabular"><Roll value={seconds(board?.goliath.p50_latency_ms)} /></td>
            <td className="tabular">
              <Roll value={usd(board?.goliath.cost_usd ?? 0)} />
              {round?.goliath.price && (
                <span className={s.amortized}>
                  tarifa: ${round.goliath.price.input_per_million.toFixed(2)} / ${round.goliath.price.output_per_million.toFixed(2)} por M tokens
                </span>
              )}
            </td>
          </tr>
        </tbody>
      </table>
      <div className={s.voteBox}>
        {showVotes ? (
          <>
            <span className="eyebrow">{voting ? "Votos en vivo" : "Votos de la ronda"} · <span className="tabular">{total}</span></span>
            <div className={s.bar} role="img" aria-label={total ? `David ${pct}%, Goliath ${100 - pct}%` : "Sin votos todavía"}>
              {total ? (
                <>
                  <span className={s.barDavid} style={{ width: `${pct}%` }}>{pct}%</span>
                  <span className={s.barGoliath}>{100 - pct}%</span>
                </>
              ) : (
                <span className={s.barEmpty}>{voting ? "Esperando votos del público" : "Sin votos"}</span>
              )}
            </div>
          </>
        ) : (
          <span className={s.voteHint}>{board?.rounds ? `${board.rounds} ${board.rounds === 1 ? "ronda" : "rondas"} · ${board.draws} ${board.draws === 1 ? "empate" : "empates"}` : "Sin rondas todavía"}</span>
        )}
        {audience && audienceUrl && round && (
          <span className={s.miniQr}>
            <Qr url={audienceUrl} size={104} />
            <span className={s.miniQrText}>Vota<br />aquí</span>
          </span>
        )}
      </div>
    </section>
  );
}

function ControlBar({
  canSwitch,
  queue,
  problem,
  voting,
  composer,
  onCompose,
  onCloseComposer,
}: {
  canSwitch: boolean;
  queue: QueuedPhrase[];
  problem: string | null;
  voting: boolean;
  composer: boolean;
  onCompose: (phrase: string, direction: Direction) => void;
  onCloseComposer: () => void;
}) {
  const [text, setText] = useState("");
  const [direction, setDirection] = useState<Direction>("genz_to_parent");
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (composer) input.current?.focus();
  }, [composer]);

  if (composer) {
    return (
      <form
        className={s.controls}
        onSubmit={(e) => {
          e.preventDefault();
          if (text.trim()) onCompose(text.trim(), direction);
          setText("");
        }}
        onKeyDown={(e) => e.key === "Escape" && onCloseComposer()}
      >
        <button type="button" className={s.dirToggle} onClick={() => setDirection((d) => (d === "genz_to_parent" ? "parent_to_genz" : "genz_to_parent"))}>
          {DIRECTION[direction]}
        </button>
        <input ref={input} className={s.composer} value={text} onChange={(e) => setText(e.target.value)} placeholder="Escribe una frase y pulsa Enter · Esc para cancelar" maxLength={240} />
      </form>
    );
  }
  return (
    <footer className={s.controls}>
      {problem ? (
        <span className={s.problem} role="alert">{problem}</span>
      ) : (
        <span className={s.next}>
          {queue[0] ? <>Siguiente del público: <b>{queue[0].text}</b></> : "Sin frases del público aprobadas"}
        </span>
      )}
      <span className={s.keys}>
        <kbd>E</kbd> set de prueba <kbd>G</kbd> especialidad chapín <kbd>↵</kbd> siguiente del público {voting && (<><kbd>V</kbd> cerrar votos</>)} <kbd>/</kbd> escribir {canSwitch && (<><kbd>M</kbd> mes pasado / este mes</>)} <kbd>F</kbd> pantalla completa
      </span>
    </footer>
  );
}
