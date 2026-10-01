// Drives the presenter side while a real Android emulator (Chrome) plays the audience:
//   node e2e/emulator-round.mjs <webUrl> <presenterUrl> "<phrase sent from the emulator>"
// Approves the phrase in /admin, duels it on the stage, then waits for the emulator's vote.
import { chromium } from "@playwright/test";

const [web, presenterUrl, phrase] = process.argv.slice(2);
const duel = process.env.DUEL_URL ?? "http://127.0.0.1:8787";
const browser = await chromium.launch();
// App Check: headless browsers can't pass reCAPTCHA, so tests use the registered debug token.
const debug = process.env.APPCHECK_DEBUG_TOKEN;
const withAppCheck = async (ctx) => {
  if (debug) await ctx.addInitScript((t) => localStorage.setItem("genlingo.appcheckDebug", t), debug);
  return ctx;
};
const stage = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await stage.goto(`${presenterUrl}/presenter`);
const admin = await (await withAppCheck(await browser.newContext())).newPage();
await admin.goto(`${web}/admin`);
await admin.fill("input[type=email]", process.env.E2E_ADMIN_EMAIL);
await admin.fill("input[type=password]", process.env.E2E_ADMIN_PASSWORD);
await admin.click("button:has-text('Entrar')");
const row = admin.locator("li", { hasText: phrase });
await row.waitFor({ timeout: 30000 });
const t0 = Date.now();
await row.locator("button:has-text('Aprobar')").click();
await stage.waitForSelector(`text=${phrase}`, { timeout: 10000 });
console.log(`approved -> stage: ${Date.now() - t0} ms`);
await stage.keyboard.press("Enter");
await stage.waitForSelector("text=Votos en vivo", { timeout: 20000 });
console.log("ROUND_OPEN");
await stage.waitForSelector("text=Votos en vivo · 1", { timeout: 120000 });
await stage.screenshot({ path: "e2e/shots/emulator-stage-vote.png" });
await stage.keyboard.press("v");
await stage.waitForTimeout(1500);
const board = await (await fetch(`${duel}/scoreboard`)).json();
console.log(`closed: david votes ${board.david.votes}, goliath votes ${board.goliath.votes}`);
await browser.close();
