/**
 * First filter before anything reaches the presenter's queue (the presenter still approves
 * every phrase). Blocks insults and slurs, and personal data (links, @handles, phone numbers):
 * the big screen is public.
 *
 * Normalization defeats the usual tricks: accents, repeated letters and leetspeak
 * ("p3nd3j00" -> "pendejo").
 */

const BLOCKED_WORDS = [
  "puta", "puto", "putas", "putos", "hijueputa", "hijodeputa", "malparido", "malparida", "gonorrea",
  "pendejo", "pendeja", "verga", "vergas", "culero", "culera", "cabron", "cabrona", "mierda",
  "maricon", "marica", "joto", "puñal", "zorra", "perra", "coño", "chingada", "chingado",
  "chingatumadre", "mamaguevo", "playo", "culo", "pija", "pajero", "idiota", "imbecil",
  "estupido", "estupida", "retrasado", "retrasada", "mongolico", "sidoso", "nazi", "negrata",
  "sudaca", "violar", "violacion", "porno", "suicidate",
];

const LEET: Record<string, string> = { "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", $: "s" };

export function normalize(text: string): string {
  return text
    .toLowerCase()
    .replace(/[0-9@$]/g, (c) => LEET[c] ?? c)
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
const WORDS = new Set(BLOCKED_WORDS.map(normalize));
// "pendejoo" -> "pendejo". Only applied to tokens that have a doubled letter, so "pera" (pear)
// never matches "perra".
const COLLAPSED = new Set([...WORDS].map(collapse));
const isBlocked = (token: string) => WORDS.has(token) || (/(.)\1/.test(token) && COLLAPSED.has(collapse(token)));
const PERSONAL_DATA = [
  { re: /(https?:\/\/|www\.|\b[\w-]+\.(com|net|org|gt|mx|co|io|ly)\b)/i, reason: "enlace" },
  { re: /(^|\s)@\w{2,}/, reason: "usuario" },
  { re: /(\+?\d[\d\s-]{6,}\d)/, reason: "teléfono" },
];

/** Returns the reason a text is blocked, or null if it may go to the presenter's queue. */
export function blockedReason(text: string): string | null {
  for (const { re, reason } of PERSONAL_DATA) if (re.test(text)) return reason;
  const tokens = normalize(text).split(" ");
  for (let i = 0; i < tokens.length; i++) {
    if (isBlocked(tokens[i])) return "lenguaje";
    // joined trigrams catch "hijo de puta" written as separate words
    if (i + 2 < tokens.length && isBlocked(tokens[i] + tokens[i + 1] + tokens[i + 2])) return "lenguaje";
  }
  return null;
}
