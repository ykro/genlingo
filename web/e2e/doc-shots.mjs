// Screenshots for the README with the real stage pair (this month's David and last month's).
//   node e2e/doc-shots.mjs <presenterBase> <audienceUrl> <outDir> [step]
// step: "online" (welcome, evaluation round, last month's David, audience phone) or "offline"
// (run with the duel service started with FORCE_OFFLINE=1). The duel service URL comes from DUEL_URL.
import { chromium, devices } from "@playwright/test";

const [base = "http://127.0.0.1:3000", audience = base, out = "../docs/screenshots", step = "online"] = process.argv.slice(2);
const duel = process.env.DUEL_URL ?? "http://127.0.0.1:8787";
const browser = await chromium.launch();
const stage = await browser.newPage({ viewport: { width: 1920, height: 1080 } });

async function waitRound(prevCount) {
  // A round is done when the duel service has one more round than before.
  for (let i = 0; i < 120; i++) {
    const rounds = await (await fetch(`${duel}/rounds?limit=50`)).json();
    if (rounds.length > prevCount) return;
    await stage.waitForTimeout(250);
  }
  throw new Error("round did not finish");
}
const count = async () => (await (await fetch(`${duel}/rounds?limit=50`)).json()).length;

async function typed(phrase) {
  const n = await count();
  await stage.keyboard.press("/");
  await stage.keyboard.type(phrase);
  await stage.keyboard.press("Enter");
  await waitRound(n);
  await stage.waitForTimeout(1800); // reveal animation
}

if (step === "online") {
  await fetch(`${duel}/reset`, { method: "POST" });
  await stage.goto(`${base}/presenter`);
  await stage.waitForTimeout(2500);
  await stage.screenshot({ path: `${out}/presentador-inicio.png` });

  let n = await count();
  await stage.keyboard.press("e");
  await waitRound(n);
  await stage.waitForTimeout(1800);
  await stage.screenshot({ path: `${out}/presentador-ronda.png` });

  await stage.keyboard.press("m"); // last month's David
  await stage.waitForTimeout(600);
  await typed("no manches, la peli estuvo bien mid y me dio cringe");
  await stage.screenshot({ path: `${out}/presentador-mes-pasado.png` });
  await stage.keyboard.press("m");

  const phone = await browser.newPage({ ...devices["Pixel 7"] });
  await phone.goto(audience);
  await phone.waitForSelector("h1", { timeout: 20000 });
  await phone.waitForTimeout(1500);
  await phone.screenshot({ path: `${out}/audiencia.png` });
} else {
  await fetch(`${duel}/reset`, { method: "POST" });
  await stage.goto(`${base}/presenter`);
  await stage.waitForTimeout(2500);
  await typed("ese bolo anda chupando desde la tarde, qué pena con los vecinos");
  await stage.screenshot({ path: `${out}/presentador-sin-internet.png` });
}
await browser.close();
console.log(`ok (${step})`);
