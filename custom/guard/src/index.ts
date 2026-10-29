import { Plugin } from "@opencode/plugin"
import { appendFileSync, mkdirSync, readFileSync } from "node:fs"
import { dirname } from "node:path"
import { homedir } from "node:os"

type Mode = "block" | "warn"

interface GuardOptions {
  mode?: Mode
  allow?: string[]
  auditLog?: string
  protectedExtensions?: string[]
  protectedNames?: string[]
  protectedDirs?: string[]
  logAll?: boolean
  injectNotice?: boolean
}

const DEFAULT_AUDIT_LOG = `${homedir()}/.local/share/opencode/audit/tool-audit.log`

const DEFAULT_EXTENSIONS = [".pem", ".key", ".p12", ".pfx", ".keystore", ".jks", ".ppk", ".asc"]

const DEFAULT_NAMES = [
  "auth.json",
  "mcp-auth.json",
  "service.json",
  "credentials.json",
  "service-account.json",
  ".netrc",
  ".npmrc",
  ".git-credentials",
  "id_rsa",
  "id_ecdsa",
  "id_ed25519",
]

const DEFAULT_DIRS = ["secrets", ".ssh"]

const SAFE_ENV_SUFFIXES = ["example", "sample", "template", "dist", "defaults", "md", "txt"]

const WRITE_TOOLS = new Set(["write", "edit", "patch", "multiedit", "apply_patch", "str_replace_editor"])
const COMMAND_TOOLS = new Set(["shell", "bash"])

const PATH_KEYS = [
  "filePath",
  "path",
  "file",
  "target",
  "paths",
  "files",
  "absolute_path",
  "notebook_path",
  "source",
  "destination",
]

const READ_COMMANDS =
  /\b(cat|less|more|head|tail|grep|rg|awk|sed|cut|strings|xxd|od|base64|printenv|source|dotenv|cp|scp|tar|zip|unzip)\b/

const NOTICE = [
  "Secret guard is active for this workspace.",
  "Files holding credentials (.env, secrets/, *.pem, *.key, auth.json, mcp-auth.json, service.json, credentials.json, ~/.ssh) are protected.",
  "Do not attempt to read them; ask the user to allow a specific path instead.",
].join(" ")

function basename(target: string): string {
  const cleaned = target.split(/[?#]/)[0]
  const index = cleaned.lastIndexOf("/")
  return index === -1 ? cleaned : cleaned.slice(index + 1)
}

function segments(target: string): string[] {
  return target.split(/[\\/]+/).filter(Boolean)
}

function matchesAllow(target: string, allow: string[]): boolean {
  return allow.some((entry) => entry.length > 0 && target.includes(entry))
}

function classify(target: string, options: Required<GuardOptions>): string | undefined {
  const base = basename(target)
  const lower = base.toLowerCase()

  if (lower === ".env") return "arquivo .env"
  if (lower.startsWith(".env.")) {
    const suffix = lower.slice(5)
    if (!SAFE_ENV_SUFFIXES.includes(suffix)) return "arquivo .env.*"
  }

  if (options.protectedNames.includes(lower)) return `nome protegido (${base})`

  for (const extension of options.protectedExtensions) {
    if (lower.endsWith(extension)) return `extensão protegida (${extension})`
  }

  for (const segment of segments(target)) {
    if (options.protectedDirs.includes(segment.toLowerCase())) return `diretório protegido (${segment})`
  }

  if (/^id_(rsa|ecdsa|ed25519)/.test(lower)) return "chave privada"
  if (lower.endsWith(".pub")) return undefined

  return undefined
}

function collectTargets(tool: string, input: Record<string, unknown>): string[] {
  const found: string[] = []
  for (const key of PATH_KEYS) {
    const value = input[key]
    if (typeof value === "string" && value.length > 0) found.push(value)
    if (Array.isArray(value)) {
      for (const item of value) if (typeof item === "string" && item.length > 0) found.push(item)
    }
  }
  if (COMMAND_TOOLS.has(tool) && typeof input.command === "string") found.push(input.command)
  return found
}

function commandLooksSensitive(command: string): boolean {
  return /(\.env\b|\/secrets\/|\/\.ssh\/|auth\.json|mcp-auth\.json|service\.json|credentials\.json|\.netrc|\.npmrc|id_rsa|\.(pem|key|p12|pfx|jks)\b)/.test(
    command,
  )
}

export default Plugin.define({
  id: "guard",
  async setup(ctx) {
    const raw = (ctx.options ?? {}) as GuardOptions
    const options: Required<GuardOptions> = {
      mode: raw.mode === "warn" ? "warn" : "block",
      allow: Array.isArray(raw.allow) ? raw.allow : [],
      auditLog: raw.auditLog ?? DEFAULT_AUDIT_LOG,
      protectedExtensions: raw.protectedExtensions ?? DEFAULT_EXTENSIONS,
      protectedNames: raw.protectedNames ?? DEFAULT_NAMES,
      protectedDirs: raw.protectedDirs ?? DEFAULT_DIRS,
      logAll: raw.logAll === true,
      injectNotice: raw.injectNotice !== false,
    }

    const stats = { blocked: 0, warned: 0, logged: 0 }

    function audit(entry: Record<string, unknown>): void {
      stats.logged += 1
      try {
        mkdirSync(dirname(options.auditLog), { recursive: true })
        appendFileSync(options.auditLog, JSON.stringify({ ts: new Date().toISOString(), ...entry }) + "\n")
      } catch {
        // audit failures must never break the session
      }
    }

    await ctx.tool.hook("execute.before", (event) => {
      const tool = String((event as { tool?: unknown }).tool ?? "")
      const input = ((event as { input?: unknown }).input ?? {}) as Record<string, unknown>
      const targets = collectTargets(tool, input)

      for (const target of targets) {
        const isCommand = COMMAND_TOOLS.has(tool)
        if (isCommand) {
          if (!READ_COMMANDS.test(target) || !commandLooksSensitive(target)) continue
        } else {
          if (!target.includes("/") && !target.startsWith(".")) continue
        }

        const reason = classify(target, options)
        if (!reason) continue
        if (matchesAllow(target, options.allow)) {
          audit({ tool, target, decision: "allowed-by-config", reason })
          continue
        }

        const isWrite = WRITE_TOOLS.has(tool)

        if (isWrite) {
          audit({ tool, target, decision: "write-logged", reason })
          continue
        }

        if (options.mode === "warn") {
          stats.warned += 1
          audit({ tool, target, decision: "warned", reason })
          continue
        }

        stats.blocked += 1
        audit({ tool, target, decision: "blocked", reason })
        void ctx.storage.set("stats", { ...stats })
        throw new Error(
          [
            `BLOCKED by the opencode-guard plugin: ${tool} on "${target}" was refused because it holds credentials (${reason}).`,
            "Do not retry or work around this block.",
            "Ask the user to allow this path by adding it to plugins[].options.allow in ~/.config/opencode/opencode.json,",
            "or by switching options.mode to \"warn\".",
          ].join(" "),
        )
      }

      if (options.logAll) audit({ tool, target: targets.join(" "), decision: "observed" })
    })

    await ctx.session.hook("context", (event) => {
      if (!options.injectNotice) return
      event.system.push({ type: "text", text: NOTICE })
    })

    await ctx.tool.transform((editor) => {
      editor.namespace({
        name: "guard",
        description: "Inspect the secret guard policy and audit counters",
      })
      editor.add({
        name: "status",
        description:
          "Show the active secret-guard policy (protected patterns, allowlist, audit log path and counters). Never returns secret values.",
        input: { type: "object", properties: {}, additionalProperties: false },
        options: { namespace: "guard" },
        execute: async () => {
          const stored = (await ctx.storage.get("stats")) as Record<string, unknown> | undefined
          const counters = { ...stats, ...(stored ?? {}) }
          return {
            content: JSON.stringify(
              {
                mode: options.mode,
                auditLog: options.auditLog,
                allow: options.allow,
                protectedExtensions: options.protectedExtensions,
                protectedNames: options.protectedNames,
                protectedDirs: options.protectedDirs,
                counters,
              },
              null,
              2,
            ),
          }
        },
      })
    })

    await ctx.command.transform((editor) => {
      editor.add({
        name: "guard-audit",
        description: "Show the last secret-guard audit entries (blocked and logged sensitive accesses)",
        execute: async ({ sessionID }) => {
          let tail = "(log inexistente)"
          try {
            const raw = readFileSync(options.auditLog, "utf8").trim()
            const lines = raw.length > 0 ? raw.split("\n") : []
            tail = lines.slice(-20).join("\n") || "(log vazio)"
          } catch {
            tail = "(log inexistente)"
          }
          await ctx.session.synthetic({
            sessionID,
            text: `Secret guard - últimas entradas de auditoria (${options.auditLog}):\n\n${tail}`,
          })
        },
      })
    })
  },
})
