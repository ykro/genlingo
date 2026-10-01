// End-to-end rehearsal of the audience flow with several simulated phones.
//   node e2e/audience-flow.mjs [webUrl] [adminUrl]
// Needs: the duel service with AUDIENCE_FEED=1 (MOCK_AI=1 is fine), the web app, and
// E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD (a presenter account) in the environment.
import { chromium, devices } from "@playwright/test";

const web = process.argv[2] ?? "http://localhost:3000";
const presenterUrl = process.argv[3] ?? "http://localhost:3000";
const duel = process.env.DUEL_URL ?? "http://127.0.0.1:8787";
const out = "e2e/shots";
const phrase = `ya me voy, está bien random todo esto ${Date.now() % 1000}`;
const ok = (cond, msg) => {
  if (!cond) throw new Error(`FALLÓ: ${msg}`);
  console.log(`✓ ${msg}`);
};

const browser = await chromium.launch();
await fetch(`${duel}/reset`, { method: "POST" });

// Presenter view (stage)
const stage = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await stage.goto(`${presenterUrl}/presenter`);
await stage.waitForSelector("text=En línea", { timeout: 20000 });

// Four phones (different devices, each its own anonymous identity)
const models = ["Pixel 7", "iPhone 13", "Galaxy S9+", "iPhone SE"];
const phones = [];
for (const m of models) {
  const ctx = await browser.newContext({ ...devices[m] });
  const p = await ctx.newPage();
  await p.goto(web);
  phones.push(p);
}
for (const p of phones) await p.waitForSelector("h1", { timeout: 30000 });
ok(true, `${phones.length} teléfonos dentro (anónimos)`);

// Phone 1 sends a phrase; the 20 s rule kicks in right away.
await phones[0].fill("#phrase", phrase);
await phones[0].click("button:has-text('Enviar')");
await phones[0].waitForSelector("text=En la fila", { timeout: 10000 });
ok(true, "frase enviada desde el teléfono 1");
await phones[0].fill("#phrase", "otra frase al hilo");
ok(await phones[0].isDisabled("form button:not([type=button])"), "el teléfono 1 debe esperar 20 s para otra frase");

// Phone 2 tries something the blocklist stops.
await phones[1].fill("#phrase", "eres un p3nd3j0");
await phones[1].click("button:has-text('Enviar')");
await phones[1].waitForSelector("text=no pasa el filtro", { timeout: 10000 });
ok(true, "la lista de bloqueo frena la frase del teléfono 2");

// Presenter approves it in /admin.
const admin = await browser.newPage({ viewport: { width: 1280, height: 860 } });
await admin.goto(`${web}/admin`);
await admin.fill("input[type=email]", process.env.E2E_ADMIN_EMAIL);
await admin.fill("input[type=password]", process.env.E2E_ADMIN_PASSWORD);
await admin.click("button:has-text('Entrar')");
const row = admin.locator("li", { hasText: phrase });
await row.waitFor({ timeout: 30000 });
await admin.screenshot({ path: `${out}/admin-queue.png` });
const t0 = Date.now();
await row.locator("button:has-text('Aprobar')").click();

// It must reach the stage screen in < 3 s.
await stage.waitForSelector(`text=${phrase}`, { timeout: 10000 });
const reach = Date.now() - t0;
ok(reach < 3000, `frase aprobada en pantalla en ${reach} ms (< 3 s)`);
await stage.screenshot({ path: `${out}/flow-queued.png` });

// Duel it; phones get the round and vote: 3 for David, 1 for Goliath.
await stage.keyboard.press("Enter");
await stage.waitForSelector("text=Votos en vivo", { timeout: 20000 });
for (const p of phones) await p.waitForSelector("button:has-text('Votar por David')", { timeout: 15000 });
ok(true, "los 4 teléfonos reciben la ronda");
await phones[0].screenshot({ path: `${out}/flow-phone-round.png` });
for (const [i, p] of phones.entries()) await p.click(i < 3 ? "button:has-text('Votar por David')" : "button:has-text('Votar por Goliath')");
for (const p of phones) await p.waitForSelector("text=Votaste por", { timeout: 10000 });
await phones[3].screenshot({ path: `${out}/flow-phone-voted.png` });
await stage.waitForSelector("text=75%", { timeout: 10000 });
ok(true, "el marcador muestra 75 % / 25 % en vivo");
await stage.screenshot({ path: `${out}/flow-votes.png` });

// Close the vote: David wins the round.
await stage.keyboard.press("v");
await stage.waitForTimeout(1500);
const board = await (await fetch(`${duel}/scoreboard`)).json();
ok(board.david.wins === 1 && board.david.votes === 3 && board.goliath.votes === 1, "al cerrar, David gana la ronda 3–1");
await stage.screenshot({ path: `${out}/flow-closed.png` });
await phones[1].waitForSelector("text=ya cerró", { timeout: 10000 }).catch(() => undefined);

await browser.close();
console.log("FLUJO OK");
