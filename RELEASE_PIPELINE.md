# AoS Revival Legacy Release Pipeline

The release path now targets the original game layout instead of an external launcher.

## Build

```powershell
.\build.ps1 --version 0.1.0
```

Or directly:

```powershell
python tools\build_release.py --version 0.1.0
```

## Output

The build writes:

- `build/releases/AoSRevival-<version>-win32/`
- `build/artifacts/AoSRevival-<version>-win32-full.zip`
- `build/artifacts/AoSRevival-<version>-pkg-only.zip`

The staged release now looks like the original packaging model:

- `aos.exe`
- `aos.pkg`
- native `.pyd` and `.dll` files
- loose game assets like `png/`, `maps/`, `sounds/`, and `mesh/`
- no shipped `python/` runtime folder
- no shipped `steam_emu*` files
- no external launcher dependency

## Notes

- The build bootstraps a Python 2-compatible PyInstaller toolchain under `build/py2toolchain/`.
- `aos.pkg` contains the Python-side game code, so small code-only updates can usually focus on that one file.
- `AoSRevival-<version>-pkg-only.zip` exists for that smaller patch workflow.
- Steam remains the intended launcher and update surface.
