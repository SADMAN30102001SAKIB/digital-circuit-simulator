import argparse
import sys
from pathlib import Path

ALLOW_PLUGINS = {
    "platforms": {"qwindows.dll"},
    "imageformats": {"qsvg.dll", "qico.dll"},
}

KEEP_TRANSLATIONS = {"qt_en.qm", "qt_help_en.qm"}


def find_pyside_roots(dist_path: Path):
    roots = []
    for p in dist_path.rglob("PySide6"):
        if p.is_dir():
            roots.append(p)
    return roots


def prune_root(root: Path, dry_run: bool = True):
    removed = []

    plugins_dir = root / "plugins"
    if plugins_dir.exists():
        # iterate plugin subfolders
        for folder in plugins_dir.iterdir():
            if not folder.is_dir():
                continue
            allowlist = ALLOW_PLUGINS.get(folder.name, set())
            for dll in folder.glob("*.dll"):
                if dll.name.lower() in allowlist:
                    continue
                # safe to delete other dlls
                removed.append(dll)
                if not dry_run:
                    try:
                        dll.unlink()
                    except Exception as e:
                        print(f"Warning: failed to remove {dll}: {e}")

    # translations
    trans_dir = root / "translations"
    if trans_dir.exists():
        for qm in trans_dir.glob("*.qm"):
            if qm.name in KEEP_TRANSLATIONS:
                continue
            removed.append(qm)
            if not dry_run:
                try:
                    qm.unlink()
                except Exception as e:
                    print(f"Warning: failed to remove {qm}: {e}")

    return removed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dist_path", type=Path, help="Path to the built onedir (e.g. dist/MyApp)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting",
    )
    args = parser.parse_args()

    dist_path = args.dist_path
    if not dist_path.exists():
        print(f"Error: dist path '{dist_path}' does not exist")
        sys.exit(2)

    roots = find_pyside_roots(dist_path)
    if not roots:
        print(f"No PySide6 trees found under {dist_path}")
        print(
            "If you expected plugins/translations in the build, ensure you built with --onedir and that PySide6 plugins were collected."
        )
        sys.exit(0)

    print(f"Found {len(roots)} PySide6 tree(s):")
    for r in roots:
        print(" -", r)

    total_removed = []
    for r in roots:
        removed = prune_root(r, dry_run=args.dry_run)
        total_removed.extend(removed)

    if not total_removed:
        print("No files matched the conservative removal rules. Nothing to do.")
        return

    print(
        "\nThe following files would be removed:"
        if args.dry_run
        else "\nRemoved the following files:"
    )
    for p in total_removed:
        print(" -", p)

    if args.dry_run:
        print("\nDry-run complete. Re-run without --dry-run to perform deletions.")
    else:
        print("\nPrune complete.")


if __name__ == "__main__":
    main()
