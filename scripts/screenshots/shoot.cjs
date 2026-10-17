/* Makes the README images in docs/images from the real panel with demo data.

   Needs Node and Playwright with Chromium:
     npm i -D playwright && npx playwright install chromium
     node scripts/screenshots/shoot.cjs
*/
const fs = require("fs");
const http = require("http");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "../..");
const OUT = path.join(ROOT, "docs", "images");
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".png": "image/png", ".svg": "image/svg+xml" };
// A fixed evening, so the images are the same every time.
const NOW = new Date("2026-10-15T20:15:00+02:00");

function serve() {
  const server = http.createServer((req, res) => {
    const file = path.join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname));
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404).end();
      return;
    }
    res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream" });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve(server)));
}

async function open(browser, base, query, { width, height, scale = 2, motion = "reduce" }) {
  const page = await browser.newPage({
    viewport: { width, height }, deviceScaleFactor: scale, locale: "da-DK", timezoneId: "Europe/Copenhagen", reducedMotion: motion,
  });
  await page.clock.setFixedTime(NOW);
  page.on("pageerror", (err) => console.error("page error:", err.message));
  await page.goto(`${base}/scripts/screenshots/demo.html?${query}`);
  await page.waitForSelector('body[data-ready="1"]');
  return page;
}

async function shot(page, selector, file, pad = 0) {
  const el = page.locator("ev-guest-panel").locator(selector).first();
  const box = await el.boundingBox();
  await page.screenshot({
    path: path.join(OUT, file),
    clip: { x: Math.max(0, box.x - pad), y: Math.max(0, box.y - pad), width: box.width + 2 * pad, height: box.height + 2 * pad },
  });
  console.log("wrote", file);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const server = await serve();
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch();
  const only = process.argv[2];

  const desktop = { width: 1280, height: 1180 };
  if (!only || only === "desktop") {
    let page = await open(browser, base, "scene=planned&theme=light", desktop);
    await page.screenshot({ path: path.join(OUT, "panel.png") });
    console.log("wrote panel.png");
    await shot(page, ".hero", "dial.png", 8);
    await shot(page, ".guest", "guest.png");
    await shot(page, ".charging", "charging.png");
    await shot(page, ".prices", "prices.png");
    await shot(page, ".facts", "facts.png");
    await page.close();

    page = await open(browser, base, "scene=charging&theme=dark", desktop);
    await page.screenshot({ path: path.join(OUT, "panel-dark.png") });
    console.log("wrote panel-dark.png");
    await page.close();

    page = await open(browser, base, "scene=planned&theme=light&tab=history", { width: 1280, height: 900 });
    await page.screenshot({ path: path.join(OUT, "history.png") });
    console.log("wrote history.png");
    await page.close();

    page = await open(browser, base, "scene=planned&theme=light&tab=history&bill=1", { width: 900, height: 860 });
    await page.screenshot({ path: path.join(OUT, "bill.png") });
    console.log("wrote bill.png");
    await page.close();

    page = await open(browser, base, "scene=planned&theme=light&tab=settings", { width: 1280, height: 1000 });
    await page.screenshot({ path: path.join(OUT, "settings.png") });
    console.log("wrote settings.png");
    await page.close();
  }

  if (!only || only === "phone") {
    for (const [scene, theme, file] of [
      ["planned", "light", "phone-plan.png"],
      ["charging", "dark", "phone-charging.png"],
    ]) {
      const page = await open(browser, base, `scene=${scene}&theme=${theme}`, { width: 390, height: 844, scale: 3 });
      await page.screenshot({ path: path.join(OUT, file) });
      console.log("wrote", file);
      await page.close();
    }
  }

  await browser.close();
  server.close();
})();
