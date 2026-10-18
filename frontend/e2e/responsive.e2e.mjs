// Layout check at phone and tablet widths: screenshots + "no sideways scrolling" + "nothing sticks out of the screen" checks.
// Run: npm run build:web && SHOTS=/tmp/rs node e2e/responsive.e2e.mjs
import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { existsSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { files, installMocks, makeFiles } from "./mocks.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const dist = join(here, "..", "dist-web");
const PORT = 4181, BASE = `http://127.0.0.1:${PORT}/`;
const exe = ["/opt/pw-browsers/chromium-1194/chrome-linux/chrome"].find(existsSync);
const shots = process.env.SHOTS || "/tmp/rs"; mkdirSync(shots, { recursive: true });
const SIZES = [["phone", 390, 844], ["small", 360, 740], ["tablet", 768, 1024], ["tablet-land", 1024, 768]];
const only = process.env.ONLY ? process.env.ONLY.split(",") : null;

const server = spawn("python3", ["-m", "http.server", String(PORT), "--bind", "127.0.0.1", "--directory", dist], { stdio: "ignore" });
await new Promise((r) => setTimeout(r, 800));
makeFiles();
const browser = await chromium.launch({ executablePath: exe, args: ["--no-sandbox"] });
let bad = 0;

/** Checks the page and every iframe: no horizontal scroll, and no visible element wider than the screen. */
async function audit(page, label) {
  const frames = page.frames();
  for (const f of frames) {
    const r = await f.evaluate(() => {
      const w = document.documentElement.clientWidth, out = [];
      const sw = Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0);
      for (const el of document.querySelectorAll("body *")) {
        const cs = getComputedStyle(el);
        if (cs.display === "none" || cs.visibility === "hidden" || cs.position === "fixed") continue;
        const b = el.getBoundingClientRect();
        if (b.width < 2 || b.height < 2) continue;
        // ignore things inside a scroll container that scrolls on purpose
        let p = el.parentElement, scroller = false;
        while (p && p !== document.body) { const o = getComputedStyle(p); if (/(auto|scroll)/.test(o.overflowX) && p.scrollWidth > p.clientWidth + 1) { scroller = true; break; } p = p.parentElement; }
        if (scroller) continue;
        if (b.right > w + 1 || b.left < -1) out.push(`${el.tagName.toLowerCase()}.${String(el.className).split(" ")[0]} [${Math.round(b.left)}..${Math.round(b.right)}] of ${w}`);
      }
      return { w, sw, out: out.slice(0, 6) };
    }).catch(() => null);
    if (!r) continue;
    const name = f === page.mainFrame() ? "page" : "iframe";
    if (r.sw > r.w + 1 || r.out.length) { bad++; console.log(`  FAIL ${label} (${name}): scrollWidth ${r.sw} > ${r.w}`, r.out.join(" | ")); }
  }
}

for (const [name, W, H] of SIZES) {
  if (only && !only.includes(name)) continue;
  console.log(`\n== ${name} ${W}x${H}`);
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, hasTouch: W < 800, isMobile: W < 800, acceptDownloads: true });
  await installMocks(ctx);
  await ctx.addInitScript(() => { try { if (!sessionStorage.getItem("tour_seen")) { sessionStorage.setItem("tour_seen", "1"); } else { localStorage.setItem("aia_tour_done", "1"); } } catch {} });
  const page = await ctx.newPage();
  const snap = async (n) => { await page.waitForTimeout(350); await page.screenshot({ path: join(shots, `${name}-${n}.png`) }); await audit(page, `${name}/${n}`); };
  await page.goto(BASE); await page.waitForSelector("h1");
  await snap("01-landing");
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2)); await snap("01b-landing-mid");
  await page.goto(BASE + "#/guide"); await page.waitForSelector("h1"); await snap("02-guide");
  await page.goto(BASE); await page.waitForSelector("h1");
  await page.getByRole("button", { name: "Sign in with Google" }).first().click();
  await page.waitForFunction(() => location.hash.startsWith("#/app"), null, { timeout: 20000 });
  await page.waitForSelector(".shell", { timeout: 30000 });
  await snap("03-home");
  const go = async (label, hash, n, wait) => { await page.goto(BASE + hash); await page.waitForTimeout(600); if (wait) await page.waitForSelector(wait, { timeout: 30000 }).catch(() => undefined); await snap(n); };
  await go("make", "#/app/make", "04-make", ".composer");
  await page.locator(".frames .slot input[type=file]").first().setInputFiles(files.image).catch(() => undefined);
  await page.waitForTimeout(800); await snap("04b-make-start-picture");
  await go("motion", "#/app/motion", "05-motion", "main");
  await go("library", "#/app/library", "06-library", "main");
  await go("editor", "#/app/editor", "07-editor", "main");
  await go("settings", "#/app/settings", "08-settings", "main");
  await page.locator(".nav-toggle").click().catch(() => undefined); await snap("08b-workspace-menu-open");
  await page.keyboard.press("Escape"); await page.waitForTimeout(400);
  await go("assistant", "#/app/assistant", "09-assistant", "iframe");
  await page.waitForTimeout(2500); await snap("09b-assistant-loaded");
  const af = page.frames().find((f) => f !== page.mainFrame());
  if (af) {
    await af.getByRole("button", { name: /Skip tour/ }).click().catch(() => undefined); await page.waitForTimeout(300); await snap("09c-assistant-no-tour");
    await af.locator(".menu-btn").click().catch(() => undefined); await page.waitForTimeout(400); await snap("09d-assistant-menu-open");
    await af.locator(".side-scrim").click({ position: { x: 360, y: 400 } }).catch(() => undefined); await page.waitForTimeout(400);
    for (const t of ["Create", "Files", "Tools", "Settings"]) {
      await af.locator(".menu-btn").click().catch(() => undefined); await page.waitForTimeout(350);
      const b = af.getByRole("button", { name: new RegExp("^" + t) }).first();
      const l = af.getByRole("link", { name: new RegExp("^" + t) }).first();
      const el = (await b.count()) ? b : l;
      if (await el.count()) { await el.click().catch(() => undefined); await page.waitForTimeout(500); await snap(`10-assistant-${t.toLowerCase()}`); }
    }
  }
  await ctx.close();
}
await browser.close(); server.kill();
console.log(bad ? `\n${bad} layout problem(s)` : "\nNo layout problems found");
process.exit(0);
