from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import tarfile
import textwrap
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = ROOT / "build"
ARTIFACTS_ROOT = BUILD_ROOT / "artifacts"
RELEASES_ROOT = BUILD_ROOT / "releases"
LEGACY_BUILD_ROOT = BUILD_ROOT / "legacy_runtime"
TOOLCHAIN_ROOT = BUILD_ROOT / "py2toolchain"
TOOLCHAIN_DOWNLOADS = TOOLCHAIN_ROOT / "downloads"
TOOLCHAIN_VENDOR = TOOLCHAIN_ROOT / "vendor"
TOOLCHAIN_SHIMS = TOOLCHAIN_ROOT / "shims"
TOOLCHAIN_CONFIG = TOOLCHAIN_ROOT / "config"

PY2_PYTHON = ROOT / "python" / "python.exe"
PYINSTALLER_ENTRY = TOOLCHAIN_VENDOR / "PyInstaller-3.5" / "pyinstaller.py"
ICON_PNG_SOURCES = [
    ROOT / "png" / "ui" / "aos16.png",
    ROOT / "png" / "ui" / "aos32.png",
    ROOT / "png" / "ui" / "aos64.png",
    ROOT / "png" / "ui" / "aos128.png",
]

PRODUCT_NAME = "AoS Revival"
MANIFEST_NAME = "build_manifest.json"
PKG_MANIFEST_NAME = "pkg_manifest.json"
VERSION_FILENAME = "version.txt"

TOOLCHAIN_COMPONENTS = [
    {
        "name": "PyInstaller-3.5",
        "archive": "PyInstaller-3.5.tar.gz",
        "url": "https://files.pythonhosted.org/packages/source/P/PyInstaller/PyInstaller-3.5.tar.gz",
    },
    {
        "name": "altgraph-0.17",
        "archive": "altgraph-0.17.tar.gz",
        "url": "https://files.pythonhosted.org/packages/source/a/altgraph/altgraph-0.17.tar.gz",
    },
    {
        "name": "pywin32-ctypes-0.2.0",
        "archive": "pywin32-ctypes-0.2.0.tar.gz",
        "url": "https://files.pythonhosted.org/packages/source/p/pywin32-ctypes/pywin32-ctypes-0.2.0.tar.gz",
    },
    {
        "name": "pefile-2017.11.5",
        "archive": "pefile-2017.11.5.tar.gz",
        "url": "https://files.pythonhosted.org/packages/source/p/pefile/pefile-2017.11.5.tar.gz",
    },
    {
        "name": "dis3-0.1.2",
        "archive": "dis3-0.1.2.tar.gz",
        "url": "https://files.pythonhosted.org/packages/source/d/dis3/dis3-0.1.2.tar.gz",
    },
    {
        "name": "future-0.18.2",
        "archive": "future-0.18.2.tar.gz",
        "url": "https://files.pythonhosted.org/packages/source/f/future/future-0.18.2.tar.gz",
    },
]

PYTHONPATH_ENTRIES = [
    TOOLCHAIN_SHIMS,
    TOOLCHAIN_VENDOR / "future-0.18.2" / "src",
    TOOLCHAIN_VENDOR / "PyInstaller-3.5",
    TOOLCHAIN_VENDOR / "altgraph-0.17",
    TOOLCHAIN_VENDOR / "pywin32-ctypes-0.2.0",
    TOOLCHAIN_VENDOR / "pefile-2017.11.5",
    TOOLCHAIN_VENDOR / "dis3-0.1.2",
]

ASSET_DIRECTORIES = [
    "ambients",
    "fonts",
    "hosted_ugc",
    "kv6",
    "maps",
    "mesh",
    "music",
    "playlists",
    "png",
    "prefabs",
    "skins",
    "sounds",
    "tga",
    "ugc",
]

EXTRA_RUNTIME_FILES = [
    "ALURE32.dll",
    "api_interfaces_32.txt",
    "codex.dll",
    "config.txt",
    "enet.pyd",
    "GameOverlayRenderer.dll",
    "libsndfile-1.dll",
    "list.pnq",
    "steam_appid.txt",
    "steamclient.dll",
]

PKG_RESOURCES_SHIM = '''from __future__ import absolute_import

import os
import pkgutil
import re
import sys
from distutils.version import LooseVersion


class DistributionNotFound(Exception):
    pass


class UnknownExtra(Exception):
    pass


class VersionConflict(Exception):
    pass


class NullProvider(object):
    def __init__(self, module):
        self.module = module


try:
    ImpWrapper = pkgutil.ImpImporter
except AttributeError:
    ImpWrapper = object


_LOADER_TYPES = {}
_VERSION_RE = re.compile(r'^(<=|>=|==|!=|<|>)(.+)$')
_NAME_RE = re.compile(r'[-_.]+')


def register_loader_type(loader_type, provider_type):
    _LOADER_TYPES[loader_type] = provider_type


def declare_namespace(package_name):
    module = sys.modules.get(package_name)
    if module is None:
        module = __import__(package_name, fromlist=['__path__'])

    module_path = getattr(module, '__path__', None)
    if module_path is None:
        return []

    module.__path__ = pkgutil.extend_path(module_path, package_name)
    return module.__path__


def normalize_name(name):
    return _NAME_RE.sub('-', (name or '')).lower()


def parse_version(version):
    return LooseVersion(str(version or '0'))


class Requirement(object):
    def __init__(self, project_name, specs=None, extras=None):
        self.project_name = project_name
        self.key = normalize_name(project_name)
        self.specs = specs or []
        self.extras = extras or set()

    @classmethod
    def parse(cls, requirement):
        requirement = (requirement or '').strip()
        name_part = requirement
        spec_part = ''
        for marker in ('<=', '>=', '==', '!=', '<', '>'):
            idx = requirement.find(marker)
            if idx != -1:
                name_part = requirement[:idx]
                spec_part = requirement[idx:]
                break

        extras = set()
        name_part = name_part.strip()
        if '[' in name_part and ']' in name_part:
            base, extra_text = name_part.split('[', 1)
            extras = set(filter(None, [item.strip() for item in extra_text.rstrip(']').split(',')]))
            name_part = base

        specs = []
        if spec_part:
            for raw_spec in spec_part.split(','):
                raw_spec = raw_spec.strip()
                if not raw_spec:
                    continue
                match = _VERSION_RE.match(raw_spec)
                if match:
                    specs.append((match.group(1), match.group(2).strip()))

        return cls(name_part.strip(), specs, extras)

    def __contains__(self, version):
        current = parse_version(version)
        for operator, target in self.specs:
            wanted = parse_version(target)
            if operator == '==' and not (current == wanted):
                return False
            if operator == '!=' and not (current != wanted):
                return False
            if operator == '>=' and not (current >= wanted):
                return False
            if operator == '<=' and not (current <= wanted):
                return False
            if operator == '>' and not (current > wanted):
                return False
            if operator == '<' and not (current < wanted):
                return False
        return True


class Distribution(object):
    def __init__(self, project_name, version, location, egg_info=None, requirements=None, metadata=None):
        self.project_name = project_name
        self.key = normalize_name(project_name)
        self.version = version or '0'
        self.location = location
        self.egg_info = egg_info
        self.parsed_version = parse_version(self.version)
        self._requirements = requirements or []
        self._metadata = metadata or {}

    def has_metadata(self, name):
        if name in self._metadata:
            return True
        if self.egg_info:
            return os.path.exists(os.path.join(self.egg_info, name))
        return False

    def get_metadata(self, name):
        if name in self._metadata:
            return self._metadata[name]
        if self.egg_info:
            metadata_path = os.path.join(self.egg_info, name)
            if os.path.exists(metadata_path):
                with open(metadata_path, 'rb') as handle:
                    return handle.read().decode('utf-8', 'ignore')
        raise IOError(name)

    def egg_name(self):
        return '%s-%s' % (self.project_name, self.version)

    def requires(self):
        return [item if isinstance(item, Requirement) else Requirement.parse(item) for item in self._requirements]


def _parse_metadata_file(metadata_path):
    project_name = None
    version = None
    requires = []
    if not os.path.exists(metadata_path):
        return project_name, version, requires
    with open(metadata_path, 'rb') as handle:
        for raw_line in handle.readlines():
            line = raw_line.decode('utf-8', 'ignore').strip()
            if line.startswith('Name:') and not project_name:
                project_name = line.split(':', 1)[1].strip()
            elif line.startswith('Version:') and not version:
                version = line.split(':', 1)[1].strip()
            elif line.startswith('Requires-Dist:'):
                requires.append(line.split(':', 1)[1].strip())
    return project_name, version, requires


def _distribution_from_path(path):
    if not path or not os.path.exists(path):
        return None

    if os.path.isdir(path) and (path.endswith('.dist-info') or path.endswith('.egg-info')):
        metadata_path = os.path.join(path, 'METADATA')
        if not os.path.exists(metadata_path):
            metadata_path = os.path.join(path, 'PKG-INFO')
        project_name, version, requires = _parse_metadata_file(metadata_path)
        if project_name:
            return Distribution(project_name, version, os.path.dirname(path), egg_info=path, requirements=requires)

    if os.path.isdir(path):
        pkg_info = os.path.join(path, 'PKG-INFO')
        if os.path.exists(pkg_info):
            project_name, version, requires = _parse_metadata_file(pkg_info)
            if project_name:
                return Distribution(project_name, version, path, egg_info=path, requirements=requires)

    return None


def find_distributions(path, only=False):
    seen = set()
    direct = _distribution_from_path(path)
    if direct is not None:
        seen.add((direct.key, direct.location))
        yield direct
    if os.path.isdir(path):
        try:
            names = os.listdir(path)
        except OSError:
            names = []
        for name in names:
            candidate = _distribution_from_path(os.path.join(path, name))
            if candidate is not None:
                marker = (candidate.key, candidate.location)
                if marker not in seen:
                    seen.add(marker)
                    yield candidate


def _iter_search_paths():
    for entry in sys.path:
        if entry:
            yield entry


def get_distribution(requirement):
    parsed = requirement if isinstance(requirement, Requirement) else Requirement.parse(requirement)
    wanted_key = parsed.key

    if wanted_key == 'pyinstaller':
        for entry in _iter_search_paths():
            if os.path.basename(entry).lower().startswith('pyinstaller-'):
                return Distribution('PyInstaller', '3.5', entry, egg_info=entry)

    for entry in _iter_search_paths():
        for dist in find_distributions(entry):
            if dist.key == wanted_key:
                if dist.version in parsed:
                    return dist
                raise VersionConflict('%s %s does not satisfy %s' % (dist.project_name, dist.version, requirement))
    raise DistributionNotFound(requirement)


def require(*requirements):
    return [get_distribution(requirement) for requirement in requirements]


def get_importer(path_item):
    return pkgutil.get_importer(path_item)


class WorkingSet(object):
    def __init__(self, entries=None):
        self.entries = list(entries or sys.path)
        self.by_key = {}
        for entry in self.entries:
            for dist in find_distributions(entry):
                self.by_key.setdefault(dist.key, dist)

    def __iter__(self):
        return iter(self.by_key.values())


working_set = WorkingSet()
'''

SPEC_TEMPLATE = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis([{run_script!r}],
             pathex=[{root!r}],
             binaries=[],
             datas=[],
             hiddenimports={hiddenimports!r},
             hookspath=[],
             runtime_hooks=[],
             excludes=['Tkinter', '_tkinter', 'FixTk', 'setuptools', 'future', 'builtins'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
release_exe = EXE(pyz,
                  a.scripts,
                  [],
                  exclude_binaries=True,
                  name='aos',
                  debug=False,
                  bootloader_ignore_signals=False,
                  strip=False,
                  upx=True,
                  console=False,
                  icon={icon_source!r},
                  pkgname='aos.pkg',
                  append_pkg=False)
debug_exe = EXE(pyz,
                a.scripts,
                [],
                exclude_binaries=True,
                name='aos_debug',
                debug=True,
                bootloader_ignore_signals=False,
                strip=False,
                upx=True,
                console=True,
                icon={icon_source!r},
                pkgname='aos.pkg',
                append_pkg=False)
coll = COLLECT(release_exe,
               debug_exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='aos')
'''

DEBUG_BAT = '@echo off\r\nstart "" aos_debug.exe %*\r\n'


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def release_name(version: str) -> str:
    return f'AoSRevival-{version}-win32'


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def download_file(url: str, destination: Path) -> None:
    ensure_directory(destination.parent)
    if destination.exists():
        return
    with urllib.request.urlopen(url) as response, destination.open('wb') as handle:
        shutil.copyfileobj(response, handle)


def extract_archive(archive_path: Path, destination: Path) -> None:
    ensure_directory(destination)
    if archive_path.suffix == '.whl' or archive_path.suffix == '.zip':
        with zipfile.ZipFile(archive_path, 'r') as archive:
            archive.extractall(destination)
    else:
        with tarfile.open(archive_path, 'r:*') as archive:
            archive.extractall(destination)


def ensure_toolchain_component(component: dict[str, str]) -> None:
    target = TOOLCHAIN_VENDOR / component['name']
    if target.exists():
        return
    archive_path = TOOLCHAIN_DOWNLOADS / component['archive']
    download_file(component['url'], archive_path)
    extract_archive(archive_path, TOOLCHAIN_VENDOR)


def write_pkg_resources_shim() -> None:
    ensure_directory(TOOLCHAIN_SHIMS)
    shim_path = TOOLCHAIN_SHIMS / 'pkg_resources.py'
    shim_path.write_text(PKG_RESOURCES_SHIM, encoding='utf-8')


def patch_pyinstaller_sources() -> None:
    bindepend_path = TOOLCHAIN_VENDOR / 'PyInstaller-3.5' / 'PyInstaller' / 'depend' / 'bindepend.py'
    bindepend_text = bindepend_path.read_text(encoding='utf-8')
    bindepend_text = bindepend_text.replace('(pefilename, exception)', '(pefilename, exc)')
    bindepend_old = "    except pefile.PEFormatError as exc:\n        raise SystemExit('Can not get architecture from file: %s\\n'\n                         '  Reason: %s' % (pefilename, exc))\n    return match_arch\n"
    bindepend_new = "    except pefile.PEFormatError:\n        return False\n    return match_arch\n"
    if bindepend_old in bindepend_text:
        bindepend_text = bindepend_text.replace(bindepend_old, bindepend_new)
    bindepend_path.write_text(bindepend_text, encoding='utf-8')

    api_path = TOOLCHAIN_VENDOR / 'PyInstaller-3.5' / 'PyInstaller' / 'building' / 'api.py'
    api_text = api_path.read_text(encoding='utf-8')
    api_variants = [
        "        self.pkgname = base_name + '.pkg'\n",
        "        pkg_base_name = base_name\n"
        "        if is_win and pkg_base_name.lower().endswith('.exe'):\n"
        "            pkg_base_name = os.path.splitext(pkg_base_name)[0]\n"
        "        self.pkgname = pkg_base_name + '.pkg'\n",
    ]
    api_new = (
        "        pkgname = kwargs.get('pkgname', None)\n"
        "        if pkgname:\n"
        "            self.pkgname = pkgname\n"
        "        else:\n"
        "            pkg_base_name = base_name\n"
        "            if is_win and pkg_base_name.lower().endswith('.exe'):\n"
        "                pkg_base_name = os.path.splitext(pkg_base_name)[0]\n"
        "            self.pkgname = pkg_base_name + '.pkg'\n"
    )
    if api_new not in api_text:
        for api_old in api_variants:
            if api_old in api_text:
                api_text = api_text.replace(api_old, api_new)
                break
        else:
            raise RuntimeError('Could not patch PyInstaller api.py pkgname block')
    api_path.write_text(api_text, encoding='utf-8')

    rthooks_path = TOOLCHAIN_VENDOR / 'PyInstaller-3.5' / 'PyInstaller' / 'loader' / 'rthooks.dat'
    rthooks_text = rthooks_path.read_text(encoding='utf-8')
    twisted_hook = "    'twisted.internet.reactor':        ['pyi_rth_twisted.py'],\n"
    if twisted_hook in rthooks_text:
        rthooks_text = rthooks_text.replace(twisted_hook, '')
        rthooks_path.write_text(rthooks_text, encoding='utf-8')


def ensure_toolchain() -> None:
    for directory in (BUILD_ROOT, TOOLCHAIN_DOWNLOADS, TOOLCHAIN_VENDOR, TOOLCHAIN_CONFIG):
        ensure_directory(directory)
    for component in TOOLCHAIN_COMPONENTS:
        ensure_toolchain_component(component)
    write_pkg_resources_shim()
    patch_pyinstaller_sources()
    if not PYINSTALLER_ENTRY.exists():
        raise RuntimeError(f'PyInstaller entry not found at {PYINSTALLER_ENTRY}')


def read_png_size(payload: bytes) -> tuple[int, int]:
    if payload[:8] != b'\x89PNG\r\n\x1a\n':
        raise RuntimeError('Expected PNG payload for icon generation')
    return int.from_bytes(payload[16:20], 'big'), int.from_bytes(payload[20:24], 'big')


def write_icon_file(icon_path: Path) -> Path:
    ensure_directory(icon_path.parent)
    entries: list[tuple[int, int, int, int]] = []
    payloads: list[bytes] = []
    offset = 6 + len(ICON_PNG_SOURCES) * 16

    for png_path in ICON_PNG_SOURCES:
        if not png_path.exists():
            raise RuntimeError(f'Icon PNG source not found at {png_path}')
        payload = png_path.read_bytes()
        width, height = read_png_size(payload)
        if width != height:
            raise RuntimeError(f'Icon PNG must be square: {png_path}')
        entries.append((width, height, len(payload), offset))
        payloads.append(payload)
        offset += len(payload)

    with icon_path.open('wb') as handle:
        handle.write(struct.pack('<HHH', 0, 1, len(entries)))
        for width, height, size, image_offset in entries:
            handle.write(
                struct.pack(
                    '<BBBBHHII',
                    0 if width >= 256 else width,
                    0 if height >= 256 else height,
                    0,
                    0,
                    1,
                    32,
                    size,
                    image_offset,
                )
            )
        for payload in payloads:
            handle.write(payload)

    return icon_path


def resolve_icon_source() -> str:
    return str(write_icon_file(LEGACY_BUILD_ROOT / 'spec' / 'aos.ico'))


def collect_hidden_imports() -> list[str]:
    hidden_imports = {path.stem for path in ROOT.glob('*.pyd')}

    for package_root in (ROOT / 'aoslib', ROOT / 'shared'):
        if not package_root.exists():
            continue
        for file_path in package_root.rglob('*.pyd'):
            relative_parts = file_path.relative_to(ROOT).with_suffix('').parts
            hidden_imports.add('.'.join(relative_parts))
            hidden_imports.add('.'.join(relative_parts[1:]))

    return sorted(name for name in hidden_imports if name)


def write_spec_file(spec_path: Path) -> None:
    ensure_directory(spec_path.parent)
    payload = SPEC_TEMPLATE.format(
        run_script=str(ROOT / 'run.py'),
        root=str(ROOT),
        hiddenimports=collect_hidden_imports(),
        icon_source=resolve_icon_source(),
    )
    spec_path.write_text(payload, encoding='utf-8')


def pyinstaller_env() -> dict[str, str]:
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(str(path) for path in PYTHONPATH_ENTRIES)
    env['PYINSTALLER_CONFIG_DIR'] = str(TOOLCHAIN_CONFIG)
    return env


def build_legacy_runtime() -> Path:
    if not PY2_PYTHON.exists():
        raise RuntimeError(f'Bundled Python 2 runtime not found at {PY2_PYTHON}')

    dist_root = LEGACY_BUILD_ROOT / 'dist'
    work_root = LEGACY_BUILD_ROOT / 'work'
    spec_root = LEGACY_BUILD_ROOT / 'spec'
    spec_file = spec_root / 'aos_legacy.spec'
    write_spec_file(spec_file)

    command = [
        str(PY2_PYTHON),
        str(PYINSTALLER_ENTRY),
        '-y',
        '--distpath',
        str(dist_root),
        '--workpath',
        str(work_root),
        '--specpath',
        str(spec_root),
        str(spec_file),
    ]
    subprocess.run(command, cwd=str(ROOT), env=pyinstaller_env(), check=True)
    runtime_dir = dist_root / 'aos'
    if not runtime_dir.exists():
        raise RuntimeError(f'Expected PyInstaller output at {runtime_dir}')
    return runtime_dir


def copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def flatten_extension_target(relative_path: Path) -> str:
    return '.'.join(relative_path.with_suffix('').parts) + relative_path.suffix


def copy_package_extensions(source_root: Path, stage_dir: Path) -> None:
    for file_path in source_root.rglob('*.pyd'):
        relative = file_path.relative_to(source_root)
        flattened_name = flatten_extension_target(relative)
        shutil.copy2(file_path, stage_dir / flattened_name)


def copy_assets(stage_dir: Path) -> None:
    for directory_name in ASSET_DIRECTORIES:
        source = ROOT / directory_name
        destination = stage_dir / directory_name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)


def copy_extra_runtime_files(stage_dir: Path) -> None:
    for filename in EXTRA_RUNTIME_FILES:
        source = ROOT / filename
        if source.exists():
            shutil.copy2(source, stage_dir / filename)


def ensure_debug_pkg(stage_dir: Path) -> None:
    shutil.copy2(stage_dir / 'aos.pkg', stage_dir / 'aos_debug.pkg')


def collect_manifest_entries(stage_dir: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for file_path in sorted(stage_dir.rglob('*')):
        if not file_path.is_file():
            continue
        relative = file_path.relative_to(stage_dir).as_posix()
        if relative in {MANIFEST_NAME, PKG_MANIFEST_NAME}:
            continue
        entries.append(
            {
                'path': relative,
                'size': file_path.stat().st_size,
                'sha256': compute_sha256(file_path),
            }
        )
    return entries


def write_json(path: Path, payload: dict[str, object]) -> None:
    ensure_directory(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')


def write_stage_metadata(stage_dir: Path, version: str) -> None:
    (stage_dir / VERSION_FILENAME).write_text(version, encoding='utf-8')
    (stage_dir / 'aos_debug.bat').write_text(DEBUG_BAT, encoding='utf-8')

    pkg_path = stage_dir / 'aos.pkg'
    debug_pkg_path = stage_dir / 'aos_debug.pkg'
    write_json(
        stage_dir / PKG_MANIFEST_NAME,
        {
            'version': version,
            'generated_at_utc': utc_now_iso(),
            'packages': [
                {
                    'path': 'aos.pkg',
                    'size': pkg_path.stat().st_size,
                    'sha256': compute_sha256(pkg_path),
                },
                {
                    'path': 'aos_debug.pkg',
                    'size': debug_pkg_path.stat().st_size,
                    'sha256': compute_sha256(debug_pkg_path),
                },
            ],
        },
    )
    write_json(
        stage_dir / MANIFEST_NAME,
        {
            'product_name': PRODUCT_NAME,
            'version': version,
            'generated_at_utc': utc_now_iso(),
            'files': collect_manifest_entries(stage_dir),
        },
    )


def stage_release(runtime_dir: Path, version: str) -> Path:
    stage_dir = RELEASES_ROOT / release_name(version)
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    ensure_directory(stage_dir)

    copy_tree(runtime_dir, stage_dir)

    include_dir = stage_dir / 'Include'
    if include_dir.exists():
        shutil.rmtree(include_dir)

    copy_package_extensions(ROOT / 'aoslib', stage_dir)
    copy_package_extensions(ROOT / 'shared', stage_dir)
    copy_assets(stage_dir)
    copy_extra_runtime_files(stage_dir)
    ensure_debug_pkg(stage_dir)
    write_stage_metadata(stage_dir, version)
    return stage_dir


def zip_directory(source_dir: Path, zip_path: Path) -> Path:
    if zip_path.exists():
        zip_path.unlink()
    ensure_directory(zip_path.parent)
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(source_dir.rglob('*')):
            if not file_path.is_file():
                continue
            archive.write(file_path, arcname=file_path.relative_to(source_dir).as_posix())
    return zip_path


def build_pkg_only_artifact(stage_dir: Path, version: str) -> Path:
    pkg_stage = BUILD_ROOT / 'pkg_only' / version
    if pkg_stage.exists():
        shutil.rmtree(pkg_stage)
    ensure_directory(pkg_stage)
    for filename in ('aos.pkg', 'aos_debug.pkg', VERSION_FILENAME, PKG_MANIFEST_NAME):
        shutil.copy2(stage_dir / filename, pkg_stage / filename)
    artifact_path = ARTIFACTS_ROOT / f'AoSRevival-{version}-pkg-only.zip'
    return zip_directory(pkg_stage, artifact_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build legacy AoS Revival releases with aos.exe + aos.pkg')
    parser.add_argument('--version', required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_directory(BUILD_ROOT)
    ensure_directory(ARTIFACTS_ROOT)
    ensure_directory(RELEASES_ROOT)

    ensure_toolchain()
    runtime_dir = build_legacy_runtime()
    stage_dir = stage_release(runtime_dir, args.version)
    full_artifact = zip_directory(stage_dir, ARTIFACTS_ROOT / f'{release_name(args.version)}-full.zip')
    pkg_artifact = build_pkg_only_artifact(stage_dir, args.version)

    print(f'Built legacy runtime: {runtime_dir}')
    print(f'Built release stage: {stage_dir}')
    print(f'Built full artifact: {full_artifact}')
    print(f'Built pkg-only artifact: {pkg_artifact}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
