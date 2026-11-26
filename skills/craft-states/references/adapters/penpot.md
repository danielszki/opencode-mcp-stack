# Adapter: Penpot

Use the [official Penpot MCP server](https://help.penpot.app/mcp/). Open the target design file and connect it from the Penpot MCP menu (remote) or the MCP plugin (local). Keep that tab open. Run `high_level_overview` for API guidance, then verify `penpot.currentFile` and `penpot.currentPage` names and IDs in a read-only `execute_code` call before editing. Use the intended Penpot session on each call when the server supports session selection. Otherwise keep only the target file connected. If the target disconnects, reconnect and verify it again. Use `penpot_api_info` and check availability in the connected plugin before relying on version-dependent API members.

| Skill verb | In Penpot |
|---|---|
| Read the design system | Inspect `penpot.library.local` and `penpot.library.connected` for components and styles. Read token sets, active themes and values from `penpot.library.local.tokens` when available. |
| Read exact values | Read shape and text properties and applied tokens with `execute_code`. Use plain objects with the relevant IDs and values as results. |
| Draw a state sheet | After scope approval, use `penpot.createBoard()` on the active page for each agreed state. Follow the state's naming scheme and position the boards side by side. Read existing board bounds first so the sheet has its own space. |
| Build a section | Use editable boards and native Flex or Grid Layout (`addFlexLayout()` / `addGridLayout()`). Append editable text and shapes and apply existing tokens with `shape.applyToken(token, properties)` where supported. |
| Reuse a piece | Find the local or connected library component by ID or full path. Call `component.instance()` and append it to the board. Keep the instance linked. |
| Make a state variant | Use `board.clone()` for each state derived from the main board. Keep dimensions, layout and shared instances when the state doesn't require changing them. Verify each clone's ID and position. |
| Look at it | Call `export_shape` with the board's ID as `shapeId` and `format: "png"` in a separate call after editing. Inspect the returned image. If export fails, use an available canvas screenshot or report the visual check as incomplete. |
