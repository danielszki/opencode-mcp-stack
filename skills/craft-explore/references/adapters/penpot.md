# Adapter: Penpot

Use the [official Penpot MCP server](https://help.penpot.app/mcp/). Open the target design file and connect it from the Penpot MCP menu (remote) or the MCP plugin (local). Keep that tab open. Run `high_level_overview` for API guidance, then verify `penpot.currentFile` and `penpot.currentPage` names and IDs in a read-only `execute_code` call before editing. Use the intended Penpot session on each call when the server supports session selection. Otherwise keep only the target file connected. If the target disconnects, reconnect and verify it again. Use `penpot_api_info` and check availability in the connected plugin before relying on version-dependent API members.

Pages must be active before building on them. After `penpot.createPage()`, set the name and await `penpot.openPage(page)` if available. Otherwise switch to the page in Penpot and verify `penpot.currentPage.id` in a new call. Use the same check when returning to an existing page.

| Skill verb | In Penpot |
|---|---|
| Read the design system | Inspect `penpot.library.local` and `penpot.library.connected` for components and styles. Read token sets, active themes and values from `penpot.library.local.tokens` when available. |
| Read exact values | Read shape and text properties and applied tokens with `execute_code`. Use plain objects with the relevant IDs and values as results. |
| Temporary exploration area | Create and activate a page named `Exploration · <topic> (temporary)`. Record its ID for cleanup. Keep existing pages untouched during exploration. |
| Build the comparison | Create a legend and equal-size top-level boards for Current (if applicable) and the proposed directions A, B, C. Use a native copy for Current where cross-page copying is available. Otherwise capture the original with `board.export({ type: "png" })` before switching pages, then upload the bytes with `penpot.uploadMediaData` and put the image in a fill on the Current board. |
| Build a section | Use editable boards and native Flex or Grid Layout (`addFlexLayout()` / `addGridLayout()`). Append editable text and shapes and apply existing tokens with `shape.applyToken(token, properties)` where supported. |
| Reuse a piece | Find the local or connected library component by ID or full path. Call `component.instance()` and append it to the board. Keep the instance linked. |
| Look at it | Call `export_shape` with the board's ID as `shapeId` and `format: "png"` in a separate call after editing. Inspect the returned image. If export fails, use an available canvas screenshot or report the visual check as incomplete. |
| Apply the pick | Return to the production page and apply the agreed changes. Remove the temporary page by its recorded ID after verifying it only holds this exploration. |
