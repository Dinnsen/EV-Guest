/* Records docs/images/<lang>/plan.gif: drag the battery, watch the plan move on the price clock, make the plan.

   Needs Node, Playwright with Chromium and Python with Pillow:
     node scripts/screenshots/record.cjs              (English)
     EVG_LANG=da node scripts/screenshots/record.cjs  (Danish)
*/
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "../..");
const NOW = new Date("2026-10-15T20:15:00+02:00");
const LANG = process.env.EVG_LANG || "en";
const TYPES = { ".html": "text/html", ".js": "text/javascript" };

function serve() {
  const server = http.createServer((req, res) => {
    const file = path.join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname));
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) return res.writeHead(404).end();
    res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream" });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve(server)));
}

(async () => {
  const frames = fs.mkdtempSync(path.join(os.tmpdir(), "evg-frames-"));
  const server = await serve();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1180, height: 900 }, deviceScaleFactor: 1, locale: LANG === "da" ? "da-DK" : "en-GB", timezoneId: "Europe/Copenhagen" });
  await page.clock.setFixedTime(NOW);
  await page.goto(`http://127.0.0.1:${server.address().port}/scripts/screenshots/demo.html?scene=planned&theme=light&lang=${LANG}`);
  await page.waitForSelector('body[data-ready="1"]');
  const panel = page.locator("ev-guest-panel");
  const hero = await panel.locator(".hero").boundingBox();
  const charging = await panel.locator(".charging").boundingBox();
  const clip = {
    x: hero.x - 10,
    y: Math.min(hero.y, charging.y) - 10,
    width: charging.x + charging.width - hero.x + 20,
    height: Math.max(hero.y + hero.height, charging.y + charging.height) - Math.min(hero.y, charging.y) + 20,
  };
  let n = 0;
  const frame = async () => page.screenshot({ path: path.join(frames, `${String(n++).padStart(4, "0")}.png`), clip });
  const hold = async (count) => { for (let i = 0; i < count; i++) { await page.waitForTimeout(70); await frame(); } };

  const cells = await panel.locator(".cells").boundingBox();
  const xAt = (pct) => cells.x + (cells.width * pct) / 100;
  const y = cells.y + cells.height / 2;
  const drag = async (from, to, steps) => {
    await page.mouse.move(xAt(from), y);
    await page.mouse.down();
    for (let i = 1; i <= steps; i++) {
      await page.mouse.move(xAt(from + ((to - from) * i) / steps), y);
      await page.waitForTimeout(40);
      await frame();
    }
    await page.mouse.up();
  };

  await hold(10);
  await drag(80, 100, 14); // target up: the window grows
  await hold(6);
  await drag(20, 45, 14); // more charge already: the window shrinks
  await hold(6);
  await panel.locator(".chips.deadline button", { hasText: /^06[:.]00$/ }).click();
  await hold(6);
  await panel.locator(".calc").click();
  await hold(22); // sweep and count up
  await browser.close();
  server.close();

  execFileSync("python3", ["-c", `
import glob, sys
from PIL import Image
files = sorted(glob.glob(sys.argv[1] + "/*.png"))
imgs = [Image.open(f).convert("RGB") for f in files]
w = 860
imgs = [i.resize((w, round(i.height * w / i.width)), Image.LANCZOS) for i in imgs]
pal = imgs[len(imgs) // 2].quantize(colors=160, method=Image.Quantize.MEDIANCUT)
q = [i.quantize(palette=pal, dither=Image.Dither.NONE) for i in imgs]
q[0].save(sys.argv[2], save_all=True, append_images=q[1:], duration=[70] * (len(q) - 1) + [2200], loop=0, optimize=True)
print(len(q), "frames")
`, frames, path.join(ROOT, "docs", "images", LANG, "plan.gif")], { stdio: "inherit" });
  fs.rmSync(frames, { recursive: true, force: true });
})();
