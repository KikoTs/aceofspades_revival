# AoS Revival Client

AoS Revival is a source-first maintenance and revival project for the Ace of Spades standalone client.

This repo is set up to:

- run the client from source while keeping the original Windows runtime layout
- build release packages in the original `aos.exe` + `aos.pkg` format
- ship the AoS Revival launcher folded into `aos.exe` (no separate launcher process)
- talk to the aosplay.net master service for accounts, the server list, and profiles
- host local Play / Tutorial / UGC matches via the bundled BattleSpades server
- avoid shipping `steam_emu`

## Current Status

- Client-side Python source now lives in the repo as `.py`, not as project-side `.pyc`.
- The shipped runtime is still the legacy Windows client model:
  - `aos.exe`
  - `aos_debug.exe`
  - `aos.pkg`
  - `aos_debug.pkg`
- The bundled `python/` directory is used for local development and packaging, but it is not shipped in releases.

## Rights And Licensing

See [LICENSE](/G:/AoSRevival/aceofspades_nonsteam/LICENSE).

Short version:

- AoS Revival-original code and tooling are intended to be MIT-licensed.
- Original Ace of Spades assets, binaries, and proprietary upstream materials are not relicensed by this repository.
- Third-party components keep their own licenses.

## Requirements

Development and packaging are currently Windows-first.

You need:

- Windows
- a Steam-capable runtime environment for normal client use
- Python 3 on your system `PATH` for repo tools and release building
- the bundled Python 2 runtime already present in [`python/`](/G:/AoSRevival/aceofspades_nonsteam/python)
- internet access on the first build so the legacy PyInstaller toolchain can be downloaded into `build/py2toolchain/`

## Running The Client From Source

`launcher.py` is the entry point (it becomes `aos.exe`). It shows the launcher UI
and, when re-invoked with `+s`, boots the game via `run.py`.

### Dependencies

Install the Python 2.7 pip dependencies once (Twisted, zope.interface, toml):

```powershell
.\python\python.exe -m pip install -r requirements.txt
```

pyglet is **not** in `requirements.txt` — the client needs a specific pyglet
`1.2dev` build that is not on PyPI, so it is vendored in [`vendor/pyglet/`](vendor/pyglet).
`run.py` adds `vendor/` to `sys.path` automatically on source runs, so no extra
step is needed when you run from the repo. (If you run in a separate Python 2.7
environment, either keep `vendor/` importable or copy `vendor/pyglet` into that
environment's `site-packages`.) The native modules — `enet` and every
`aoslib`/`shared` `.pyd` — already ship in the repo.

Run the launcher:

```powershell
.\python\python.exe launcher.py
```

Skip the launcher and boot the game directly (what the launcher does internally):

```powershell
.\python\python.exe run.py
```

Debug run with logging:

```powershell
.\python\python.exe run.py +debug
```

Direct connect:

```powershell
.\python\python.exe run.py +connect 127.0.0.1:32887
```

Legacy mouse fallback:

```powershell
.\python\python.exe run.py +legacymouse
```

Useful notes:

- `run.py` is the top-level bootstrap.
- [`aoslib/run.py`](/G:/AoSRevival/aceofspades_nonsteam/aoslib/run.py) is the main client startup path.
- The raw-input compatibility patch for old pyglet lives in [`aoslib/pyglet_win32_raw_mouse.py`](/G:/AoSRevival/aceofspades_nonsteam/aoslib/pyglet_win32_raw_mouse.py).
- Debug logs are written under `logs/` when `+debug` is used.

## Building A Release

Quick build:

```powershell
.\build.ps1 --version 0.1.0
```

Direct build command:

```powershell
python tools\build_release.py --version 0.1.0
```

The release builder currently wraps the legacy build path in [`tools/build_legacy_release.py`](/G:/AoSRevival/aceofspades_nonsteam/tools/build_legacy_release.py).

### Build Output

The builder writes:

- `build/releases/AoSRevival-<version>-win32/`
- `build/artifacts/AoSRevival-<version>-win32-full.zip`
- `build/artifacts/AoSRevival-<version>-pkg-only.zip`

The staged release contains:

- `aos.exe`
- `aos_debug.exe`
- `aos.pkg`
- `aos_debug.pkg`
- native `.pyd` and `.dll` files
- loose asset folders such as `png/`, `maps/`, `mesh/`, `sounds/`, and `music/`

The staged release also includes:

- `config_user.json` (username/language read by `shared/steam.py`)
- `server/` — the bundled BattleSpades dedicated server for local matches

The shipped release does not include:

- the local `python/` runtime folder
- `steam_emu*`

## How The Repo Is Organized

Important paths:

- [`run.py`](/G:/AoSRevival/aceofspades_nonsteam/run.py): top-level client bootstrap
- [`aoslib/`](/G:/AoSRevival/aceofspades_nonsteam/aoslib): main Python-side client code
- [`shared/`](/G:/AoSRevival/aceofspades_nonsteam/shared): shared constants and gameplay support code
- [`playlists/`](/G:/AoSRevival/aceofspades_nonsteam/playlists): playlist definitions
- [`tools/`](/G:/AoSRevival/aceofspades_nonsteam/tools): import/build/cleanup scripts
- [`python/`](/G:/AoSRevival/aceofspades_nonsteam/python): bundled Python 2 runtime used for local development and packaging
- [`build/`](/G:/AoSRevival/aceofspades_nonsteam/build): generated output and temporary build toolchain data

There are also compiled native modules such as `.pyd` files under `aoslib/` and `shared/`. Those are still part of the client runtime and are not replaced by the new source cleanup.

## Working On The Client

### Normal Python-side changes

Edit the source in:

- [`aoslib/`](/G:/AoSRevival/aceofspades_nonsteam/aoslib)
- [`shared/`](/G:/AoSRevival/aceofspades_nonsteam/shared)
- [`playlists/`](/G:/AoSRevival/aceofspades_nonsteam/playlists)
- [`run.py`](/G:/AoSRevival/aceofspades_nonsteam/run.py)

Then test locally with the bundled Python 2 runtime and rebuild a legacy package when needed.

### If You Need To Resync Decompiled Source

If a project-side module is still missing real source and you have a reference tree under [`aceofspades_decompiled/`](/G:/AoSRevival/aceofspades_nonsteam/aceofspades_decompiled), use:

```powershell
python tools\import_decompiled_sources.py
```

That script will:

- copy only missing `.py` files into the repo
- strip known decompiler banners
- create small wrappers for `aoslib/strings/backup`
- delete matching repo-side `.pyc` files

It does not overwrite files that already exist as real source.

### Server List Configuration

The client-side hosted server list adapter is in [`aoslib/web.py`](/G:/AoSRevival/aceofspades_nonsteam/aoslib/web.py).

By default it uses:

- `https://aceofspades-web-server.vercel.app/serverlist`

You can override it for local testing with:

```powershell
$env:AOS_SERVER_LIST_URL = "https://example.com/serverlist"
```

### Files You Should Usually Leave Alone

- bundled runtime binaries in the repo root
- `.pyd` extension modules unless you are intentionally rebuilding native code
- the generated `build/` tree
- the local reference folders ignored by Git

## Recommended Workflow

1. Run from source with `.\python\python.exe run.py +debug`.
2. Fix or iterate on Python-side client code.
3. Rebuild a test release with `python tools\build_release.py --version <version>`.
4. Smoke-test `aos.exe` and `aos_debug.exe` from the staged release folder.
5. Publish either the full zip or the smaller `pkg-only` zip depending on the change.

## Packaging Notes

- `aos.pkg` contains the Python-side game code.
- Small client code updates can often ship as a `pkg-only` artifact.
- The release builder bootstraps a Python 2-compatible PyInstaller 3.5 toolchain automatically under `build/py2toolchain/`.
- The generated executables use the original AoS icon bundle from `png/ui/aos16.png`, `aos32.png`, `aos64.png`, and `aos128.png`.

## Related Docs

- [`RELEASE_PIPELINE.md`](/G:/AoSRevival/aceofspades_nonsteam/RELEASE_PIPELINE.md)

## Known Constraints

- The client runtime is still Python 2-based.
- Some behavior still depends on closed/native `.pyd` modules.
- Imported source recovered from historical/decompiled material may still need hand cleanup or behavior verification in places.
- This repo is designed around Windows packaging and Steam-era client behavior, not a clean-room reimplementation.
