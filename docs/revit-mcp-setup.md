# Revit MCP connection — setup (Revit 2026 test rig)

**Status: working (2026-09-30).** Claude reaches Revit 2026 (26.1) on `1268 - Kalael (R26 TEST)` through the `revit` MCP server; status, list_levels and execute_revit_code all verified read-only. `mcc_compat.eid_int` confirmed working in 2026 (`ElementId.IntegerValue` is gone there).

Purpose: let Claude read the open Revit model and run test scripts directly (via pyRevit Routes), instead of the run-button / export-PDF / report-back loop. Production stays on Revit 2023; this rig is for development only.

Server: mcp-servers-for-revit/mcp-server-for-revit-python (https://github.com/mcp-servers-for-revit/mcp-server-for-revit-python), cloned at commit 51b4829. It is both a pyRevit extension (runs inside Revit, IronPython) and a small CPython MCP server (main.py) that Claude Desktop launches via uv. Key tool: `execute_revit_code` (runs IronPython in Revit), plus model/view/level/family queries.

## Steps
1. **pyRevit for 2026** — install/update pyRevit (5.x or later; 6.5.5 installer is in the Outline Annotator folder) with Revit 2026 ticked. Confirm the MCC tab loads in 2026 (pyRevit already points at the Outline Annotator folder).
2. **Test model** — open `1268 - Kalae (R23).rvt` in 2026 (Detach from Central / Discard worksets if asked), let it upgrade, then immediately *Save As* a TEST copy (currently `1268 - Kalael (R26 TEST).rvt`). Never save over the R23 file — an upgraded file can't go back to 2023.
3. **Get the extension** — clone into the Outline Annotator folder as `RevitMCP.extension`:
   `git clone https://github.com/mcp-servers-for-revit/mcp-server-for-revit-python "C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\RevitMCP.extension"`
   pyRevit picks it up because it already scans that folder. Apply the local patches below.
4. **Turn on Routes** — pyRevit tab → Settings → Routes → enable Routes Server → Save, restart Revit. With a model open, `http://localhost:48884/revit_mcp/status/` should return `{"status": "active", ...}`. **Restart Revit rather than using pyRevit Reload** whenever Routes/extension code changes (pyRevit issue #3473).
5. **Install uv** — PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`. Installs to `C:\Users\agarcia\.local\bin\uv.exe`.
6. **Register with Claude Desktop** — Settings → Developer → Edit Config; inside the existing `mcpServers` (next to `pencil`, comma after its `}`) add:
   ```json
   "revit": {
     "command": "C:\\Users\\agarcia\\.local\\bin\\uv.exe",
     "args": ["run", "--with", "mcp[cli]<2", "--with", "httpx", "mcp", "run",
              "C:\\Users\\agarcia\\Desktop\\Claude Projects\\Outline Annotator\\RevitMCP.extension\\main.py"]
   }
   ```
   Fully quit Claude Desktop (system tray too) and reopen. Errors go to `%APPDATA%\Claude\logs\mcp-server-revit.log` (or Settings → Developer → revit → View logs).
   - Full uv path: Claude Desktop didn't find bare `uv`.
   - `--with httpx`: main.py imports httpx; the repo's README command doesn't install it.
   - `mcp[cli]<2`: the code uses `mcp.server.fastmcp` (MCP SDK v1); uv otherwise grabs v2, which renamed it. The `<2` goes *after* the `]`.
   - Don't use `--with-requirements requirements.txt`: it pins old versions that may not install on Python 3.14.
7. **Hand off to Claude** — with Revit 2026 open on the TEST model, tell Claude; tools appear as `revit__*` (status, list_levels, execute_revit_code, …).

## Local patches (re-apply after `git pull` of the extension or any pyRevit update)
- **RevitMCP.extension/extension.json** ships `"builtin": "True", "default_enabled": "False"` → pyRevit never runs `startup.py`, Routes answers `RouteHandlerNotDefinedException: Route does not exits: "GET revit_mcp/status/"`. Patched to `"builtin": "False", "default_enabled": "True"`.
- **RevitMCP.extension/revit_mcp/status.py, model_info.py** — handlers read `revit.doc` from the web-server thread. Patched to take a `doc` argument so pyRevit runs them on Revit's API thread. Originals kept as `*.py.orig`.
- **pyRevit core: `%APPDATA%\pyRevit-Master\pyrevitlib\pyrevit\routes\server\server.py`** — Revit crashed on the first /status/ request. Applied the three fixes from pyRevit PR #3558 (unreleased at the time): `HttpRequestHandler.log_message` → no-op (per-request stderr writes from a worker thread make pyRevit build its WPF output window off the STA thread → fatal crash); `ThreadedHttpServer.handle_error` → no-op (same); removed the duplicate `self.start()` in `RoutesServer.__init__`. Original kept as `server.py.orig`. **This fixed the crash.** A pyRevit update will overwrite it — check the update includes the fix first.

## Using it from code
`execute_revit_code` runs IronPython with `doc`, `uidoc`, `DB`, `revit`, `print`. No transaction is opened automatically. To import MCC lib modules:
```python
import sys
lib = r"C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\MCC.extension\lib"
if lib not in sys.path: sys.path.append(lib)
from mcc_compat import eid_int
```

## Ground rules
- Only point it at the R26 TEST copy (execute_revit_code can change anything).
- Claude runs read-only checks first; model edits only inside test runs Adolfo has agreed to.
- Routes listens on localhost only.
- Buttons still ship as the MCC pyRevit extension; code must stay IronPython 2.7 compatible (no f-strings) and 2023-safe (use `mcc_compat.eid_int`, not `IntegerValue`).
