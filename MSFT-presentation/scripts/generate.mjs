#!/usr/bin/env node
/**
 * generate.mjs — Build Marp slides to HTML + PPTX from any .md file
 *
 * Usage:
 *   node scripts/generate.mjs slides/slides.md
 *   node scripts/generate.mjs path/to/deck.md
 *   node scripts/generate.mjs slides/slides.md --pdf   # also generate PDF
 *
 * Outputs land next to the source .md:
 *   slides/slides.html
 *   slides/slides.pptx
 *   slides/slides.pdf   (with --pdf flag)
 */
import { execSync } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';

const args = process.argv.slice(2);
const mdFile = args.find(a => a.endsWith('.md'));
const wantPdf = args.includes('--pdf');

if (!mdFile) {
  console.error('Usage: node scripts/generate.mjs <path/to/slides.md> [--pdf]');
  process.exit(1);
}

if (!fs.existsSync(mdFile)) {
  console.error(`File not found: ${mdFile}`);
  process.exit(1);
}

const dir = path.dirname(mdFile);
const base = path.basename(mdFile, '.md');

// Resolve theme: check for skill-local theme first, then repo-level
const scriptDir = path.dirname(new URL(import.meta.url).pathname);
const skillRoot = path.resolve(scriptDir, '..');
const localTheme = path.join(skillRoot, 'theme', 'microsoft-internal.css');
const repoTheme = path.resolve('themes/microsoft-internal.css');
const theme = fs.existsSync(localTheme) ? localTheme : repoTheme;

if (!fs.existsSync(theme)) {
  console.error(`Theme not found. Checked:\n  ${localTheme}\n  ${repoTheme}`);
  process.exit(1);
}

// Find Playwright's Chromium for Marp browser-based exports (PPTX/PDF)
function findChromium() {
  const cacheDir = path.join(process.env.HOME || '', '.cache', 'ms-playwright');
  if (fs.existsSync(cacheDir)) {
    for (const entry of fs.readdirSync(cacheDir).sort().reverse()) {
      if (entry.startsWith('chromium-')) {
        const bin = path.join(cacheDir, entry, 'chrome-linux64', 'chrome');
        if (fs.existsSync(bin)) return bin;
      }
    }
  }
  return null;
}
const chromiumPath = findChromium();
const browserArgs = chromiumPath ? `--browser-path "${chromiumPath}"` : '';

function run(cmd) {
  console.log(`  → ${cmd}`);
  execSync(cmd, { stdio: 'inherit' });
}

console.log(`\n📄 Source:  ${mdFile}`);
console.log(`🎨 Theme:   ${theme}`);
console.log(`📁 Output:  ${dir}/\n`);

// HTML
const htmlOut = path.join(dir, `${base}.html`);
run(`npx marp "${mdFile}" -o "${htmlOut}" --theme-set "${theme}" --html`);
console.log(`  ✅ ${htmlOut}`);

// Verify HTML is self-contained (logos embedded as data URIs, no external refs)
const htmlContent = fs.readFileSync(htmlOut, 'utf-8');
const dataUriCount = (htmlContent.match(/url\(['"]?data:image/g) || []).length;
if (dataUriCount >= 2) {
  console.log(`     ✓ Self-contained (${dataUriCount} embedded images) — safe to copy folder`);
} else {
  console.log(`     ⚠ Only ${dataUriCount} embedded images — logos may be missing`);
}

// PPTX
const pptxOut = path.join(dir, `${base}.pptx`);
run(`npx marp "${mdFile}" -o "${pptxOut}" --pptx --theme-set "${theme}" --html --allow-local-files ${browserArgs}`);
console.log(`  ✅ ${pptxOut}`);

// PDF (optional)
if (wantPdf) {
  const pdfOut = path.join(dir, `${base}.pdf`);
  run(`npx marp "${mdFile}" -o "${pdfOut}" --pdf --theme-set "${theme}" --html --allow-local-files ${browserArgs}`);
  console.log(`  ✅ ${pdfOut}`);
}

console.log('\n🎉 Done\n');
