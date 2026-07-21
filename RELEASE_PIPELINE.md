# AoS Revival Legacy Release Pipeline

The release targets the original game layout (`aos.exe` + `aos.pkg`), with the
AoS Revival launcher folded into the executable — there is no separate launcher
process. `aos.exe` opens the launcher UI, and the launcher spawns the game as an
isolated child of the same executable (`aos.exe +s ...`).

## Build

```powershell
.\build.ps1 --version 0.1.0
```

Or directly:

```powershell
python tools\build_release.py --version 0.1.0
```

## Prerequisites

- A Python 2 runtime at `python\python.exe` (not committed; supply it yourself).
- Python 3 on `PATH` to run the builder, plus internet on the first build for the
  PyInstaller 3.5 toolchain.
- The bundled BattleSpades dedicated server at `..\BattleSpades\dist\BattleSpades\`
  (or point `AOS_BATTLESPADES_SERVER` at a folder containing `BattleSpades.exe`).
  This is staged into the release as `server/` so the Play / Tutorial / UGC menus
  can launch a local match. Build the BattleSpades dist first if it is missing.

## Output

The build writes:

- `build/releases/AoSRevival-<version>-win32/`
- `build/artifacts/AoSRevival-<version>-win32-full.zip`
- `build/artifacts/AoSRevival-<version>-pkg-only.zip`

The staged release contains:

- `aos.exe` / `aos_debug.exe` (these open the launcher, then boot the game child)
- `aos.pkg` / `aos_debug.pkg` (the Python-side client code, including the launcher)
- native `.pyd` and `.dll` files
- `config_user.json` (username/language identity read by `shared/steam.py`)
- loose asset folders like `png/`, `maps/`, `sounds/`, and `mesh/`
- `server/` — the bundled BattleSpades dedicated server for local play
- no shipped `python/` runtime folder
- no `steam_emu*` files

## Notes

- The PyInstaller entry point is `launcher.py`. Tkinter is bundled for the
  launcher UI. `launcher.main()` shows the launcher normally and boots the game
  when re-invoked with `+s`.
- `shared/steam.py` is a pure-Python reconstruction of the old `shared.steam`
  extension; it reads `config_user.json` and does not depend on `steam_emu.ini`.
  The compiled `shared/steam.pyd` has been removed so the source module wins.
- `aos.pkg` contains the Python-side game code, so small code-only updates can
  usually ship as `AoSRevival-<version>-pkg-only.zip`.
