// Screenshots for docs/DEMO.md, one per step, against the real stage (make up).
//   node e2e/demo-shots.mjs <presenterBase> <outDir> <step>
// steps: stage (01–05), audience (07: waits for the phrase sent from the emulator, runs it),
// previous (08), offline (09: duel service started with FORCE_OFFLINE=1). The phone screenshot
// (06) comes from the emulator itself: adb -s emulator-5556 exec-out screencap -p > 06-publico-telefono.png
import { chromium } from "@playwright/test";

const [base = "http://127.0.0.1:3000", out = "../docs/demo", step = "stage"] = process.argv.slice(2);
const duel = process.env.DUEL_URL ?? "http://127.0.0.1:8787";
const browser = await chromium.launch();
const stage = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const count = async () => (await (await fetch(`${duel}/rounds?limit=100`)).json()).length;

async function waitRound(before) {
  for (let i = 0; i < 240; i++) {
    if ((await count()) > before) return;
    await stage.waitForTimeout(250);
  }
  throw new Error("round did not finish");
}
async function keys(...seq) {
  const n = await count();
  for (const k of seq) await stage.keyboard.press(k);
  await waitRound(n);
  await stage.waitForTimeout(1800); // reveal animation
}
async function typed(phrase, { flip = false } = {}) {
  const n = await count();
  await stage.keyboard.press("/");
  await stage.waitForTimeout(200);
  if (flip) await stage.keyboard.press("Tab");
  await stage.keyboard.type(phrase);
  await stage.keyboard.press("Enter");
  await waitRound(n);
  await stage.waitForTimeout(1800);
}
const shot = (name) => stage.screenshot({ path: `${out}/${name}.png` });

await stage.goto(`${base}/presenter`);
await stage.waitForTimeout(2500);
if (step === "stage") {
  await fetch(`${duel}/reset`, { method: "POST" });
  await stage.reload();
  await stage.waitForTimeout(2500);
  await shot("01-bienvenida");
  await keys("e");
  await shot("02-ronda-evaluacion");
  await keys("g");
  await shot("03-especialidad-chapin");
  await typed("Qué onda, maje, no traigo pisto para el chinique, estoy bien pisado");
  await shot("04-genz-a-papas");
  await typed("Mijo, ese patojo es muy shute y anda armando bochinche", { flip: true });
  await shot("05-papas-a-genz");
} else if (step === "audience") {
  await stage.waitForSelector("text=en fila", { timeout: 120000 });
  await keys("Enter");
  await stage.waitForTimeout(8000); // time for the emulator's vote
  await shot("07-publico-pantalla");
} else if (step === "previous") {
  await stage.keyboard.press("m");
  await stage.waitForTimeout(800);
  await typed("no manches, la peli estuvo bien mid y me dio cringe");
  await shot("08-mes-anterior");
  await stage.keyboard.press("m");
} else if (step === "offline") {
  await typed("ese bolo anda chupando desde la tarde, qué pena con los vecinos");
  await shot("09-sin-internet");
}
await browser.close();
console.log(`ok (${step})`);
