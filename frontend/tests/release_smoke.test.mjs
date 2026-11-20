// Artefact-only release smoke check. It does not start a browser, service worker,
// device or backend, and proves nothing about real-device offline behaviour.
import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const frontendRoot = fileURLToPath(new URL('..', import.meta.url));
const distRoot = join(frontendRoot, 'dist');
const assetNames = () => readdirSync(join(distRoot, 'assets'));

function readShell() {
  const shellPath = join(distRoot, 'index.html');
  assert.ok(existsSync(shellPath), 'run npm run build before npm run test:release');
  return readFileSync(shellPath, 'utf8');
}

test('build artefacts contain the HTML route shell', () => {
  const shell = readShell();
  assert.match(shell, /<div id="root"><\/div>/);
  assert.match(shell, /<title>EcoWatch<\/title>/);
  assert.match(shell, /<link rel="manifest" href="\/manifest\.webmanifest" \/>/);
  assert.match(shell, /<script[^>]+type="module"[^>]+src="\/assets\/[^"]+\.js"/);

  const assets = assetNames();
  assert.ok(assets.some((name) => name.startsWith('index-') && name.endsWith('.js')));
  assert.ok(assets.some((name) => name.endsWith('.css')));
  for (const name of assets) {
    assert.ok(statSync(join(distRoot, 'assets', name)).size > 0, `${name} is empty`);
  }
  // Presence only: a copied service worker is not evidence of offline behaviour.
  assert.ok(existsSync(join(distRoot, 'sw.js')));
  assert.ok(existsSync(join(distRoot, 'manifest.webmanifest')));
});

test('public and staff route definitions reach the shipped bundle', () => {
  const routes = [
    '/',
    '/faq',
    '/report',
    '/track',
    '/updates',
    '/updates/:caseId',
    '/login',
    '/workspace',
    '/cases',
    '/cases/:caseId',
    '/monitoring',
    '/evidence',
    '/analysis',
    '/prioritisation',
    '/interventions',
    '/verification',
    '/admin',
  ];
  const appSource = readFileSync(join(frontendRoot, 'src', 'App.tsx'), 'utf8');
  for (const route of routes) {
    assert.ok(appSource.includes(`path="${route}"`), `route ${route} is missing from App.tsx`);
  }

  const bundle = assetNames()
    .filter((name) => name.endsWith('.js'))
    .map((name) => readFileSync(join(distRoot, 'assets', name), 'utf8'))
    .join('\n');
  for (const route of ['/faq', '/report', '/workspace', '/admin']) {
    assert.ok(bundle.includes(`"${route}"`), `route ${route} is missing from the bundle`);
  }
});
