/**
 * Generic Marp slide validator — works with any deck HTML
 *
 * Usage:
 *   node scripts/validate_slides.mjs <path/to/slides.html>
 *
 * Checks per slide:
 *   - Logo rendering (data URI)
 *   - Footer ("Microsoft Confidential")
 *   - Background color (matches class)
 *   - Font (Segoe UI)
 *   - Heading presence
 *
 * Outputs screenshots to artifacts/screenshots/validate-<timestamp>/
 */
import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs/promises';

const htmlArg = process.argv[2];
if (!htmlArg) {
  console.error('Usage: node scripts/validate_slides.mjs <path/to/slides.html>');
  process.exit(1);
}

const root = process.cwd();
const htmlPath = path.resolve(root, htmlArg);

try {
  await fs.access(htmlPath);
} catch {
  console.error(`File not found: ${htmlPath}`);
  process.exit(1);
}

const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const outDir = path.resolve(root, `artifacts/screenshots/validate-${ts}`);
const latestLink = path.resolve(root, 'artifacts/screenshots/validate-latest');

const errors = [];
const warnings = [];

function fail(msg) { errors.push(msg); console.log(`  ❌ ${msg}`); }
function warn(msg) { warnings.push(msg); console.log(`  ⚠️  ${msg}`); }
function pass(msg) { console.log(`  ✅ ${msg}`); }

console.log(`\n━━━ Validating: ${htmlArg} ━━━\n`);

let browser;
try {
  browser = await chromium.launch({
    headless: true,
    channel: 'chromium',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto(`file://${htmlPath}`);
  await page.waitForTimeout(1500);

  const slideData = await page.evaluate(() => {
    const sections = document.querySelectorAll('svg > foreignObject > section');
    return [...sections].map((s, i) => {
      const cs = getComputedStyle(s);
      const beforeBg = getComputedStyle(s, '::before').backgroundImage;
      const footer = s.querySelector('footer')?.textContent?.trim();
      const afterContent = getComputedStyle(s, '::after').content;
      const imgs = s.querySelectorAll('img');
      const brokenImgs = [...imgs].filter(img => !img.complete || img.naturalWidth === 0).length;
      return {
        index: i + 1,
        classes: s.getAttribute('class') || '',
        bgColor: cs.backgroundColor,
        textColor: cs.color,
        font: cs.fontFamily,
        hasLogo: beforeBg !== 'none',
        logoIsDataUri: beforeBg?.startsWith('url("data:'),
        footer,
        pagination: afterContent,
        headingCount: s.querySelectorAll('h1,h2,h3,h4').length,
        imageCount: imgs.length,
        brokenImages: brokenImgs,
      };
    });
  });

  console.log(`  Found ${slideData.length} slides\n`);

  // Capture screenshots
  await fs.mkdir(outDir, { recursive: true });
  await page.click('body');
  await page.waitForTimeout(300);

  for (let i = 0; i < slideData.length; i++) {
    await page.screenshot({ path: path.join(outDir, `slide-${i + 1}.png`) });
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(400);
  }

  console.log(`  Screenshots saved to ${outDir}\n`);

  // Validate each slide
  for (const d of slideData) {
    const label = `Slide ${d.index}`;

    // Logo
    if (!d.hasLogo) fail(`${label}: Logo NOT rendered`);
    else if (!d.logoIsDataUri) warn(`${label}: Logo not using data URI`);
    else pass(`${label}: Logo ✓`);

    // Footer
    if (!d.footer?.includes('Confidential')) fail(`${label}: Missing "Microsoft Confidential" footer`);
    else pass(`${label}: Footer ✓`);

    // Background color
    const isLight = d.classes.includes('light');
    const isDivider = d.classes.includes('divider');
    const expBg = isLight ? 'rgb(244, 243, 245)' : isDivider ? 'rgb(11, 39, 54)' : 'rgb(9, 31, 44)';
    if (d.bgColor !== expBg) warn(`${label}: bg=${d.bgColor} (expected ${expBg})`);
    else pass(`${label}: Background ✓`);

    // Font
    if (!d.font?.includes('Segoe')) warn(`${label}: Not using Segoe UI font`);
    else pass(`${label}: Font ✓`);

    // Heading
    if (d.headingCount === 0) warn(`${label}: No heading found`);
    else pass(`${label}: Heading ✓`);

    // Broken images
    if (d.brokenImages > 0) fail(`${label}: ${d.brokenImages} broken image(s)`);
    else if (d.imageCount > 0) pass(`${label}: ${d.imageCount} image(s) loaded ✓`);

    console.log('');
  }

  await browser.close();
} catch (e) {
  if (browser) await browser.close();
  fail(`Playwright error: ${e.message?.substring(0, 200)}`);
}

// Summary
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log(`  ERRORS:   ${errors.length}`);
console.log(`  WARNINGS: ${warnings.length}`);
if (errors.length === 0 && warnings.length === 0) {
  console.log('  🎉 ALL CHECKS PASSED');
} else if (errors.length === 0) {
  console.log('  ⚠️  Passed with warnings');
} else {
  console.log('  ❌ FAILED — fix errors above');
}
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

// Update symlink
try { await fs.rm(latestLink, { force: true }); } catch {}
try { await fs.symlink(outDir, latestLink); } catch {}

process.exit(errors.length > 0 ? 1 : 0);
