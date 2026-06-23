import { chromium } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

const url = process.env.URL ?? 'http://127.0.0.1:5173';
const outDir = new URL('../tmp/verification/', import.meta.url);

const viewports = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'mobile', width: 390, height: 844 },
];

await mkdir(outDir, { recursive: true });

const browser = await chromium.launch();
const failures = [];

for (const viewport of viewports) {
  const page = await browser.newPage({ viewport });
  const consoleErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => consoleErrors.push(error.message));

  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForSelector('canvas');
  await page.waitForTimeout(500);
  await page.locator('[data-start]').click();
  await page.waitForTimeout(900);

  const drawerState = await page.evaluate(() => ({
    runDisplay: getComputedStyle(document.querySelector('.run-panel')).display,
    movesDisplay: getComputedStyle(document.querySelector('.history-panel')).display,
  }));

  const canvasStats = await page.evaluate(() => {
    const canvas = document.querySelector('canvas');
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    const pixels = [];
    const sample = new Uint8Array(4);
    const width = gl.drawingBufferWidth;
    const height = gl.drawingBufferHeight;
    for (let y = 0.15; y <= 0.85; y += 0.14) {
      for (let x = 0.15; x <= 0.85; x += 0.14) {
        gl.readPixels(Math.floor(width * x), Math.floor(height * y), 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, sample);
        pixels.push(`${sample[0]},${sample[1]},${sample[2]},${sample[3]}`);
      }
    }
    return {
      width,
      height,
      unique: new Set(pixels).size,
      transparent: pixels.filter((pixel) => pixel.endsWith(',0')).length,
    };
  });

  const screenshot = new URL(`${viewport.name}.png`, outDir);
  await page.screenshot({ path: screenshot.pathname, fullPage: true });

  if (consoleErrors.length) failures.push(`${viewport.name} console errors: ${consoleErrors.join(' | ')}`);
  if (drawerState.runDisplay !== 'none') failures.push(`${viewport.name} run drawer is visible by default`);
  if (drawerState.movesDisplay !== 'none') failures.push(`${viewport.name} moves drawer is visible by default`);
  if (canvasStats.width < viewport.width || canvasStats.height < viewport.height) {
    failures.push(`${viewport.name} canvas is undersized: ${canvasStats.width}x${canvasStats.height}`);
  }
  if (canvasStats.unique < 8) failures.push(`${viewport.name} canvas appears too visually flat: ${canvasStats.unique} unique samples`);
  if (canvasStats.transparent > 0) failures.push(`${viewport.name} canvas has transparent sample pixels`);

  await page.close();
}

await browser.close();

if (failures.length) {
  console.error(failures.join('\n'));
  process.exit(1);
}

console.log('3D verification passed for desktop and mobile.');
