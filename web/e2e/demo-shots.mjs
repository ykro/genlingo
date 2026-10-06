// Screenshots for docs/DEMO.md: the comparison page (/traducir) served by the duel service (make up).
//   node e2e/demo-shots.mjs [duelBase] [outDir] [step]
// steps: online (10 and 11: one example per direction, both sides answered), offline (12: run the
// duel service with FORCE_OFFLINE=1 on another port and pass its base URL).
import { chromium } from "@playwright/test";

const [base = "http://127.0.0.1:8787", out = "../docs/demo", step = "online"] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(`${base}/traducir`);
await page.waitForSelector(".ex");

async function example(text) {
  await page.locator(".ex", { hasText: text }).click();
  await page.waitForFunction(() => !document.getElementById("go").disabled, null, { timeout: 90000 });
  await page.waitForTimeout(700); // entry animation
}

if (step === "online") {
  await example("chafa");
  await page.screenshot({ path: `${out}/10-comparar-genz-a-papas.png` });
  await example("refacción");
  await page.screenshot({ path: `${out}/11-comparar-papas-a-genz.png` });
} else if (step === "offline") {
  await example("pajas");
  await page.screenshot({ path: `${out}/12-sin-internet.png` });
}
await browser.close();
console.log(`ok (${step})`);
