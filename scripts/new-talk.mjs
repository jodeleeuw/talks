#!/usr/bin/env node
// Scaffold a new talk by copying template/ into a chosen location.
// Usage: ./scripts/new-talk.mjs   (or: node scripts/new-talk.mjs)

import { readdir, stat, mkdir, copyFile, readFile, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname, resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn, spawnSync } from 'node:child_process';
import { createInterface } from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const TEMPLATE = join(REPO_ROOT, 'template');

// Don't copy these out of template/
const SKIP_COPY = new Set(['node_modules', 'dist', '.slidev']);

// Don't suggest these as parent dirs for the new talk
const SKIP_BUCKET = new Set(['node_modules', 'template', 'dist', 'scripts', 'tmp_talks']);

async function findBuckets() {
  const out = ['.']; // repo root itself
  const entries = await readdir(REPO_ROOT, { withFileTypes: true });
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    if (e.name.startsWith('.')) continue;
    if (SKIP_BUCKET.has(e.name)) continue;
    // If it has slides.md, it's a talk, not a bucket
    if (existsSync(join(REPO_ROOT, e.name, 'slides.md'))) continue;
    out.push(e.name);
  }
  // tmp_talks is gitignored but useful for throwaways — always offer it
  out.push('tmp_talks');
  return out;
}

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

async function main() {
  if (!existsSync(TEMPLATE)) {
    console.error(`No template/ dir found at ${TEMPLATE}`);
    process.exit(1);
  }

  const rl = createInterface({ input, output });
  const ask = (q) => rl.question(q);

  const buckets = await findBuckets();
  console.log('\nWhere should the new talk live?\n');
  buckets.forEach((b, i) => {
    const label = b === '.' ? '. (repo root)' : `${b}/`;
    console.log(`  ${i + 1}) ${label}`);
  });
  console.log(`  n) [type a new folder name]\n`);

  let bucket;
  while (!bucket) {
    const ans = (await ask('choice: ')).trim();
    if (ans === 'n' || ans === 'N') {
      const newBucket = (await ask('new folder name: ')).trim();
      if (!validName(newBucket)) { console.log('  invalid name'); continue; }
      bucket = newBucket;
    } else {
      const idx = parseInt(ans, 10);
      if (Number.isInteger(idx) && idx >= 1 && idx <= buckets.length) {
        bucket = buckets[idx - 1];
      } else {
        console.log('  invalid choice');
      }
    }
  }

  let name;
  while (!name) {
    const ans = (await ask('\nname for the new talk folder: ')).trim();
    if (!validName(ans)) {
      console.log('  invalid (use letters, digits, dot, dash, underscore)');
      continue;
    }
    const target = join(REPO_ROOT, bucket, ans);
    if (existsSync(target)) {
      console.log(`  ${relative(REPO_ROOT, target)} already exists`);
      continue;
    }
    name = ans;
  }

  rl.close();

  const target = join(REPO_ROOT, bucket, name);
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
  const install = spawnSync('pnpm', ['install'], { cwd: target, stdio: 'inherit' });
  if (install.status !== 0) {
    console.error('pnpm install failed');
    process.exit(install.status ?? 1);
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
  console.error(err);
  process.exit(1);
});
