# Adapter: Penpot

Use the [official Penpot MCP server](https://help.penpot.app/mcp/). Open the target design file and connect it from the Penpot MCP menu (remote) or the MCP plugin (local). Keep that tab open. Run `high_level_overview` for API guidance, then verify `penpot.currentFile` and `penpot.currentPage` names and IDs in a read-only `execute_code` call before editing. Use the intended Penpot session on each call when the server supports session selection. Otherwise keep only the target file connected. If the target disconnects, reconnect and verify it again. Use `penpot_api_info` and check availability in the connected plugin before relying on version-dependent API members.

Pages must be active before building on them. After `penpot.createPage()`, set the name and await `penpot.openPage(page)` if available. Otherwise switch to the page in Penpot and verify `penpot.currentPage.id` in a new call. Use the same check when returning to an existing page.

| Skill verb | In Penpot |
|---|---|
| Read the design system | Inspect `penpot.library.local` and `penpot.library.connected` for components and styles. Read token sets, active themes and values from `penpot.library.local.tokens` when available. |
| Read exact values | Read shape and text properties and applied tokens with `execute_code`. Use plain objects with the relevant IDs and values as results. |
| Foundations | Draft the guide on its own boards. After approval, register supported token types in the owning file's editable catalog. Use `catalog.addSet({ name })` and `set.addToken({ type, name, value })` where supported. Reuse existing sets, check activation before binding, and document unsupported values on the guide. |
| Component guide | Use `penpot.library.local.createComponent([board])` for main components. Where supported, pass their `mainInstance()` boards to `penpot.createVariantFromComponents`. Name the group's variant properties and set each component's values. Show linked instances in a variants × states matrix with a legend and component index. |
| Build a section | Use editable boards and native Flex or Grid Layout (`addFlexLayout()` / `addGridLayout()`). Append editable text and shapes and apply existing tokens with `shape.applyToken(token, properties)` where supported. |
| Reuse a piece | Find the local or connected library component by ID or full path. Call `component.instance()` and append it to the board. Keep the instance linked. |
| Audit or propagate | Find affected instances by component/library ID and token bindings. Read across pages with `penpot.currentFile.pages`. Apply approved edits in the owning library, then check the affected instances in their actual pages. |
| Look at it | Call `export_shape` with the board's ID as `shapeId` and `format: "png"` in a separate call after editing. Inspect the returned image. If export fails, use an available canvas screenshot or report the visual check as incomplete. |

After changing a token, read its resolved value and the affected properties in a fresh call. If a bound property still has the old value, refresh that property. In Penpot 2.19.1, `applyToken` toggles an existing binding off. Verify the property is unbound before applying the token again, then read back the binding and value before reporting propagation.
