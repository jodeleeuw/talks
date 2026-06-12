#!/usr/bin/env node
// Scaffold a new talk by copying template/ into a chosen location.
// Usage: ./scripts/new-talk.mjs   (or: node scripts/new-talk.mjs)

import { readdir, mkdir, copyFile, readFile, writeFile } from 'node:fs/promises';
import { existsSync, readdirSync } from 'node:fs';
import { join, dirname, resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn, spawnSync } from 'node:child_process';
import { search, input } from '@inquirer/prompts';

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const TEMPLATE = join(REPO_ROOT, 'template');

// Don't copy these out of template/
const SKIP_COPY = new Set(['node_modules', 'dist', '.slidev']);

// Hide these when listing folders to navigate into
const SKIP_LIST = new Set(['node_modules', 'dist', '.slidev', '.git']);

async function copyTree(src, dest) {
  await mkdir(dest, { recursive: true });
  const entries = await readdir(src, { withFileTypes: true });
  for (const e of entries) {
    if (SKIP_COPY.has(e.name)) continue;
    const s = join(src, e.name);
    const d = join(dest, e.name);
    if (e.isDirectory()) await copyTree(s, d);
    else if (e.isFile()) await copyFile(s, d);
  }
}

function validName(n) {
  return /^[a-zA-Z0-9._-]+$/.test(n);
}

function listDirs(dir) {
  try {
    return readdirSync(dir, { withFileTypes: true })
      .filter((e) => e.isDirectory() && !e.name.startsWith('.') && !SKIP_LIST.has(e.name))
      .map((e) => e.name)
      .sort((a, b) => a.localeCompare(b));
  } catch {
    return []; // unreadable dir (permissions, etc.)
  }
}

// Navigable, searchable folder picker. Returns the absolute path of the
// directory chosen as the parent for the new talk. Type to filter the current
// folder, ⏎ to open a folder, pick "use this folder" to select the current one.
async function pickFolder(start) {
  let cwd = resolve(start);
  while (true) {
    const choice = await search({
      message: `Where should the new talk live? (${relative(REPO_ROOT, cwd) || '.'}/)`,
      source: (term) => {
        const t = (term ?? '').toLowerCase();
        const dirs = listDirs(cwd).filter((d) => d.toLowerCase().includes(t));
        const items = [{ name: '✓ use this folder', value: { action: 'use' } }];
        if (dirname(cwd) !== cwd) items.push({ name: '.. up a level', value: { action: 'up' } });
        for (const d of dirs) items.push({ name: `📁 ${d}/`, value: { action: 'open', name: d } });
        return items;
      },
    });
    if (choice.action === 'use') return cwd;
    cwd = choice.action === 'up' ? dirname(cwd) : join(cwd, choice.name);
  }
}

async function main() {
  if (!existsSync(TEMPLATE)) {
    console.error(`No template/ dir found at ${TEMPLATE}`);
    process.exit(1);
  }

  const parentDir = await pickFolder(REPO_ROOT);
  const parentRel = relative(REPO_ROOT, parentDir) || '.';

  const name = (
    await input({
      message: `name for the new talk folder (under ${parentRel}/)`,
      validate: (v) => {
        const n = v.trim();
        if (!validName(n)) return 'use letters, digits, dot, dash, underscore';
        if (existsSync(join(parentDir, n))) return `${relative(REPO_ROOT, join(parentDir, n))} already exists`;
        return true;
      },
    })
  ).trim();

  const target = join(parentDir, name);
  const rel = relative(REPO_ROOT, target);

  console.log(`\nCopying template/ → ${rel}/`);
  await copyTree(TEMPLATE, target);

  // Patch package.json "name" to match the folder
  const pkgPath = join(target, 'package.json');
  if (existsSync(pkgPath)) {
    const pkg = JSON.parse(await readFile(pkgPath, 'utf8'));
    pkg.name = name;
    await writeFile(pkgPath, JSON.stringify(pkg, null, 2) + '\n');
  }

  console.log(`\nRunning pnpm install in ${rel}/`);
  const installResult = spawnSync('pnpm', ['install'], { cwd: target, stdio: 'inherit' });
  if (installResult.status !== 0) {
    console.error('pnpm install failed');
    process.exit(installResult.status ?? 1);
  }

  const hasCode = spawnSync('sh', ['-c', 'command -v code'], { stdio: 'ignore' }).status === 0;
  if (hasCode) {
    console.log(`\nOpening ${rel}/ in VS Code`);
    spawn('code', [target], { detached: true, stdio: 'ignore' }).unref();
  }

  console.log(`\nStarting dev server — Ctrl-C to stop\n`);
  const dev = spawn('pnpm', ['dev', '--open'], { cwd: target, stdio: 'inherit' });
  dev.on('exit', (code) => process.exit(code ?? 0));
}

main().catch((err) => {
  // Ctrl-C / Esc out of an inquirer prompt
  if (err && err.name === 'ExitPromptError') {
    console.log('\ncancelled');
    process.exit(0);
  }
  console.error(err);
  process.exit(1);
});
