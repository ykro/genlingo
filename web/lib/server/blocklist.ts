/**
 * The filter before anything reaches the big screen: with AUTO_APPROVE_PHRASES=1 (the default) a
 * phrase that passes it goes straight to the presenter's queue, so it has to be strict. Blocks
 * insults and slurs, and personal data (links, @handles, phone numbers): the big screen is public.
 *
 * Normalization defeats the usual tricks: accents, repeated letters, leetspeak ("p3nd3j00"),
 * spaced or dotted letters ("p u t o", "p.e.n.d.e.j.o"), v/u/b and k/c swaps ("pvto", "berga",
 * "kabron") and the common abbreviations ("hdp", "ctm", "ptm", "alv").
 */

const BLOCKED_WORDS = [
  "puta", "puto", "putas", "putos", "hijueputa", "hijodeputa", "malparido", "malparida", "gonorrea",
  "pendejo", "pendeja", "verga", "vergas", "culero", "culera", "cabron", "cabrona", "mierda",
  "maricon", "marica", "joto", "puñal", "zorra", "perra", "coño", "chingada", "chingado",
  "chingatumadre", "mamaguevo", "playo", "culo", "pija", "pajero", "idiota", "imbecil",
  "estupido", "estupida", "retrasado", "retrasada", "mongolico", "sidoso", "nazi", "negrata",
  "sudaca", "violar", "violacion", "porno", "suicidate",
];

// Abbreviations: only blocked as whole tokens (they are too short to look for inside words).
const BLOCKED_ABBREVIATIONS = [
  "hdp", "hp", "hpta", "hpt", "ctm", "ctmr", "csm", "ptm", "ptmr", "alv", "vrg", "pndj", "pndja",
  "mmg", "mmgv", "hdlgp", "cdtm", "chtm", "qlo", "qliao", "mrd",
];

const LEET: Record<string, string> = {
  "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "6": "g", "7": "t", "8": "b", "9": "g", "@": "a", $: "s", "!": "i", "|": "l", "€": "e",
};

export function normalize(text: string): string {
  return text
    .toLowerCase()
    .replace(/[0-9@$!|€]/g, (c) => LEET[c] ?? c)
    .replace(/ñ/g, "\u0001") // keep ñ while stripping the other accents
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\u0001/g, "ñ")
    .replace(/(.)\1{2,}/g, "$1") // "puuuuto" -> "puto" (2 letters stay: "perro", "llama")
    .replace(/[^a-zñ\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const collapse = (w: string) => w.replace(/(.)\1+/g, "$1");
// Spelling swaps people use to dodge filters: v/b sound the same ("berga"), k/qu for c ("kabron").
const canon = (w: string) => w.replace(/v/g, "b").replace(/k/g, "c").replace(/qu(?=[ei])/g, "c");
const WORDS = new Set(BLOCKED_WORDS.map((w) => canon(normalize(w))));
const ABBREVIATIONS = new Set(BLOCKED_ABBREVIATIONS);
// "pendejoo" -> "pendejo". Only applied to tokens that have a doubled letter, so "pera" (pear)
// never matches "perra".
const COLLAPSED = new Set([...WORDS].map(collapse));
const isWord = (token: string) => WORDS.has(token) || (/(.)\1/.test(token) && COLLAPSED.has(collapse(token)));
/** A token is blocked as written, with v read as u ("pvto"), or after the v/b, k/c swaps. */
const isBlocked = (token: string) =>
  ABBREVIATIONS.has(token) || isWord(canon(token)) || isWord(canon(token.replace(/v/g, "u")));
/** Letters spelled out one by one ("p u t o", "p.u.t.o" after normalization): any blocked word inside. */
const spelledOut = (letters: string) =>
  letters.length >= 3 && [...WORDS].some((w) => w.length >= 3 && (canon(letters).includes(w) || canon(letters.replace(/v/g, "u")).includes(w)));
const PERSONAL_DATA = [
  { re: /(https?:\/\/|www\.|\b[\w-]+\.(com|net|org|gt|mx|co|io|ly)\b)/i, reason: "enlace" },
  { re: /(^|\s)@\w{2,}/, reason: "usuario" },
  { re: /(\+?\d[\d\s-]{6,}\d)/, reason: "teléfono" },
];

/** Returns the reason a text is blocked, or null if it may go to the screen queue. */
export function blockedReason(text: string): string | null {
  for (const { re, reason } of PERSONAL_DATA) if (re.test(text)) return reason;
  const tokens = normalize(text).split(" ");
  let run = "";
  for (let i = 0; i < tokens.length; i++) {
    if (isBlocked(tokens[i])) return "lenguaje";
    // joined trigrams catch "hijo de puta" written as separate words (no bigrams: "por no" is not "porno")
    if (i + 2 < tokens.length && isBlocked(tokens[i] + tokens[i + 1] + tokens[i + 2])) return "lenguaje";
    run = tokens[i].length === 1 ? run + tokens[i] : "";
    if (spelledOut(run)) return "lenguaje";
  }
  return null;
}
