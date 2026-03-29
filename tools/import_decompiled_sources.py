from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECOMPILED_ROOT = ROOT / 'aceofspades_decompiled'

SKIP_ROOTS = {
    '.git',
    'build',
    'python',
    'original',
    'aceofspades_decompiled',
}

BACKUP_STRINGS_DIR = Path('aoslib/strings/backup')
DECOMPILER_HEADER_PREFIXES = (
    '# uncompyle6 version ',
    '# Python bytecode version base ',
    '# Decompiled from: ',
    '# Embedded file name: ',
    '#Embedded file name: ',
)
TIMESTAMP_HEADER = re.compile(r'^# \d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\s*$')
BACKUP_SUFFIXES = (
    '.pyc_bk',
    '.pyo_bk',
    '.pyc_backup',
    '.pyo_backup',
)


@dataclass
class SyncSummary:
    imported: int = 0
    wrappers: int = 0
    deleted_bytecode: int = 0
    deleted_backups: int = 0
    unresolved: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Import missing Python sources from aceofspades_decompiled and remove project bytecode.'
    )
    parser.add_argument(
        '--decompiled-root',
        default=str(DEFAULT_DECOMPILED_ROOT),
        help='Directory containing decompiled Python sources.',
    )
    parser.add_argument(
        '--keep-pyc',
        action='store_true',
        help='Keep project-side .pyc files after importing source.',
    )
    return parser.parse_args()


def is_skipped(relative_path: Path) -> bool:
    return bool(relative_path.parts) and relative_path.parts[0] in SKIP_ROOTS


def iter_project_bytecode(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob('*.pyc')
        if not is_skipped(path.relative_to(root))
    )


def iter_backup_bytecode(root: Path) -> list[Path]:
    results: list[Path] = []
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if is_skipped(relative):
            continue
        lower_name = path.name.lower()
        if any(lower_name.endswith(suffix) for suffix in BACKUP_SUFFIXES):
            results.append(path)
    return sorted(results)


def strip_decompiler_header(text: str) -> str:
    lines = text.splitlines()
    while lines and (lines[0].startswith(DECOMPILER_HEADER_PREFIXES) or TIMESTAMP_HEADER.match(lines[0])):
        lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)
    return '\n'.join(lines).rstrip() + '\n'


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def build_backup_wrapper(relative_source: Path) -> str:
    if relative_source.name == '__init__.py':
        return 'from aoslib.strings import *\n'
    return f'from aoslib.strings.{relative_source.stem} import *\n'


def resolve_missing_source(relative_source: Path, decompiled_root: Path) -> tuple[str | None, bool]:
    decompiled_source = decompiled_root / relative_source
    if decompiled_source.exists():
        return strip_decompiler_header(read_text(decompiled_source)), False

    if relative_source.parent == BACKUP_STRINGS_DIR:
        return build_backup_wrapper(relative_source), True

    return None, False


def import_missing_sources(root: Path, decompiled_root: Path) -> SyncSummary:
    summary = SyncSummary()

    for bytecode_path in iter_project_bytecode(root):
        source_path = bytecode_path.with_suffix('.py')
        if source_path.exists():
            continue

        relative_source = source_path.relative_to(root)
        source_text, is_wrapper = resolve_missing_source(relative_source, decompiled_root)
        if source_text is None:
            print(f'UNRESOLVED {relative_source.as_posix()}')
            summary.unresolved += 1
            continue

        write_text(source_path, source_text)
        if is_wrapper:
            summary.wrappers += 1
            print(f'WRAPPED   {relative_source.as_posix()}')
        else:
            summary.imported += 1
            print(f'IMPORTED  {relative_source.as_posix()}')

    return summary


def delete_project_bytecode(root: Path) -> tuple[int, int]:
    deleted_bytecode = 0
    deleted_backups = 0

    for bytecode_path in iter_project_bytecode(root):
        if bytecode_path.with_suffix('.py').exists():
            bytecode_path.unlink()
            deleted_bytecode += 1
            print(f'DELETED   {bytecode_path.relative_to(root).as_posix()}')

    for backup_path in iter_backup_bytecode(root):
        backup_path.unlink()
        deleted_backups += 1
        print(f'DELETED   {backup_path.relative_to(root).as_posix()}')

    return deleted_bytecode, deleted_backups


def main() -> int:
    args = parse_args()
    decompiled_root = Path(args.decompiled_root).resolve()
    if not decompiled_root.exists():
        raise SystemExit(f'Decompiled root not found: {decompiled_root}')

    summary = import_missing_sources(ROOT, decompiled_root)
    if not args.keep_pyc:
        deleted_bytecode, deleted_backups = delete_project_bytecode(ROOT)
        summary.deleted_bytecode = deleted_bytecode
        summary.deleted_backups = deleted_backups

    print('')
    print('Imported sources : %d' % summary.imported)
    print('Wrapper sources  : %d' % summary.wrappers)
    print('Deleted .pyc     : %d' % summary.deleted_bytecode)
    print('Deleted backups  : %d' % summary.deleted_backups)
    print('Unresolved       : %d' % summary.unresolved)

    if summary.unresolved:
        raise SystemExit(1)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
