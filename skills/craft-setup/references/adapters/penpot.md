# Adapter: Penpot

Use the [official Penpot MCP server](https://help.penpot.app/mcp/). Open the target design file and connect it from the Penpot MCP menu (remote) or the MCP plugin (local). Keep that tab open. Run `high_level_overview` for API guidance, then verify `penpot.currentFile` and `penpot.currentPage` names and IDs in a read-only `execute_code` call before editing. Use the intended Penpot session on each call when the server supports session selection. Otherwise keep only the target file connected. If the target disconnects, reconnect and verify it again. Use `penpot_api_info` and check availability in the connected plugin before relying on version-dependent API members.

Write `DESIGN.md` in the repo. Use Penpot to inspect existing design assets and to draw the optional references board. Use `craft-system` or `craft-sync` for foundations.

Pages must be active before building on them. After `penpot.createPage()`, set the name and await `penpot.openPage(page)` if available. Otherwise switch to the page in Penpot and verify `penpot.currentPage.id` in a new call. Use the same check when returning to an existing page.

| Skill verb | In Penpot |
|---|---|
| Read what exists | List the pages with `penpot.currentFile.pages`, including any existing guide page. Inspect `penpot.library.local` and `penpot.library.connected` for components and styles, and read token sets, active themes and values from `penpot.library.local.tokens` when available. |
| References board (optional) | Make one board per reference on a `References` page, with the image and the Take and Avoid notes. Use `import_image` for local assets when the server exposes it, or use `penpot.uploadMediaUrl` / `penpot.uploadMediaData` and assign the returned image to a shape's `fillImage`. If the image is unavailable, keep the reference link and notes on the board. |
| Look at it | Call `export_shape` with the board's ID as `shapeId` and `format: "png"` in a separate call after editing. Inspect the returned image. If export fails, use an available canvas screenshot or report the visual check as incomplete. |
