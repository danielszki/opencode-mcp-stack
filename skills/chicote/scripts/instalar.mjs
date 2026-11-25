#!/usr/bin/env node
/**
 * instalar.mjs: deixa o chicote pronto para usar.
 *   1. baixa o Chromium que a chicotada e o pexels.mjs usam;
 *   2. liga a skill no Claude Code (~/.claude/skills/chicote → esta pasta), se ainda não estiver.
 *
 *   npm install && npm run instalar
 */
import { execSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
console.log("▸ Chromium para medir as páginas…");
execSync("npx playwright install chromium", { cwd: raiz, stdio: "inherit" });

const skills = path.join(os.homedir(), ".claude", "skills");
const destino = path.join(skills, "chicote");
fs.mkdirSync(skills, { recursive: true });
let estado;
try {
  const atual = fs.realpathSync(destino);
  estado = atual === raiz ? "já ligado" : `já existe e aponta para ${atual} (não mexi)`;
} catch {
  fs.symlinkSync(raiz, destino, "dir");
  estado = "ligado agora";
}
console.log(`▸ Claude Code: ${destino} → ${raiz} (${estado})`);
console.log(`
Pronto. Abra uma conversa nova no Claude Code e digite:

  /chicote <conte a história: o que é, pra quem, o que vende, referências>

Em outros agentes (Codex, Cursor…), aponte para ${path.join(raiz, "SKILL.md")}.
Para conferir que tudo mede certo: npm run teste
`);
