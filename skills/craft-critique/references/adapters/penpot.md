# Adapter: Penpot

Use the [official Penpot MCP server](https://help.penpot.app/mcp/). Open the target design file and connect it from the Penpot MCP menu (remote) or the MCP plugin (local). Keep that tab open. Run `high_level_overview` for API guidance, then verify `penpot.currentFile` and `penpot.currentPage` names and IDs in a read-only `execute_code` call before editing. Use the intended Penpot session on each call when the server supports session selection. Otherwise keep only the target file connected. If the target disconnects, reconnect and verify it again. Use `penpot_api_info` and check availability in the connected plugin before relying on version-dependent API members.

| Skill verb | In Penpot |
|---|---|
| Read the design system | Inspect `penpot.library.local` and `penpot.library.connected` for components and styles. Read token sets, active themes and values from `penpot.library.local.tokens` when available. |
| Read exact values | Read shape and text properties and applied tokens with `execute_code`. Use plain objects with the relevant IDs and values as results. |
| Review one board | Inspect its hierarchy, text, bounds, layout and component links. Get the board ID from the verified page hierarchy. Resolve the effective values of applied tokens for the active sets. |
| Look at it | Call `export_shape` with the board's ID as `shapeId` and `format: "png"` in a separate call after editing. Inspect the returned image. If export fails, use an available canvas screenshot or report the visual check as incomplete. |
| Refine or self-check | Change only findings in scope with `execute_code`. Re-read actual bounds and render again in a fresh call so layout updates have time to settle. |
