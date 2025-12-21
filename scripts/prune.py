import argparse
import sys
import platform
from pathlib import Path

# Identify Platform
IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform.startswith("darwin")
IS_LINUX = sys.platform.startswith("linux")

# Dynamic Extension
EXT = ".dll" if IS_WIN else (".dylib" if IS_MAC else ".so")
# On Linux/Mac, files often have versions like .so.6 or .dylib.1
EXT_PATTERN = f"*{EXT}" if IS_WIN else f"*{EXT}*" 
PYD_EXT = ".pyd" if IS_WIN else ".so"

REQUIRED_CORES = {
    "qt6core",
    "qt6gui",
    "qt6widgets",
    "qt6dbus",  # Explicitly preserve DBus on Linux
    "shiboken6",
    "pyside6",
    "qtcore", 
    "qtgui",
    "qtwidgets",
    "qtdbus",
}

# Substrings in DLL names that indicate they belong to unused heavy modules
UNNEEDED_DLL_FRAGMENTS = [
    "qml",
    "quick",
    "network",
    "pdf",
    "webengine",
    "multimedia",
    "webchannel",
    "websockets",
    "test",
    "sql",
    "openglbase",
    "designer",
    "help",
    "bluetooth",
    "nfc",
    "positioning",
    "sensors",
    "serialport",
    "remoteobjects",
    "charts",
    "datavisualization",
    "scxml",
    "statemachine",
    "svg",
]

# System-specific allowed plugins
PLATFORM_PLUGIN = "qwindows" if IS_WIN else ("qcocoa" if IS_MAC else "qxcb")
STYLE_PLUGIN = "qwindowsvistastyle" if IS_WIN else ("qmacstyle" if IS_MAC else None)

ALLOW_PLUGINS = {
    "platforms": {f"{PLATFORM_PLUGIN}{EXT}"},
    "imageformats": {f"qico{EXT}"},
}
if STYLE_PLUGIN:
    ALLOW_PLUGINS["styles"] = {f"{STYLE_PLUGIN}{EXT}"}

KEEP_TRANSLATIONS = {"qt_en.qm", "qt_help_en.qm"}


def find_pyside_roots(dist_path: Path):
    roots = []
    # 1. Look for the main _internal folder (Standard for newer PyInstaller)
    internal = dist_path / "_internal"
    if internal.is_dir():
        roots.append(internal)
    
    # 2. Look for any explicit PySide6 folders (Sometimes in root or _internal)
    for p in dist_path.rglob("PySide6"):
        if p.is_dir() and p not in roots:
            roots.append(p)

    return roots


def prune_root(root: Path, dry_run: bool = True):
    removed = []

    # 1. Prune root DLLs (Aggressive)
    # On Mac/Linux, we check for .dylib or .so instead of .dll
    for dll in root.glob(EXT_PATTERN):
        dll_name = dll.name.lower()
        
        # Fuzzy match for core libs (handles 'lib' prefix or versioning like .so.6)
        if any(core in dll_name for core in REQUIRED_CORES):
            continue

        # Check if it matches any unneeded fragments
        if any(frag in dll_name for frag in UNNEEDED_DLL_FRAGMENTS):
            removed.append(dll)
            if not dry_run:
                try:
                    dll.unlink()
                except Exception as e:
                    print(f"Warning: failed to remove {dll}: {e}")

    # 2. Prune Plugins (Conservative)
    plugins_dir = root / "plugins"
    if plugins_dir.exists():
        for folder in plugins_dir.iterdir():
            if not folder.is_dir():
                continue
            
            # If the folder is in our allowlist, keep the WHOLE folder
            if folder.name.lower() in ALLOW_PLUGINS:
                continue
                
            # Otherwise, it's an unused category (like 'qml' or 'multimedia' plugins)
            removed.append(folder)
            if not dry_run:
                try:
                    import shutil
                    shutil.rmtree(folder)
                except Exception as e:
                    print(f"Warning: failed to remove {folder}: {e}")

    # 3. Prune Translations
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
    parser = argparse.ArgumentParser(
        description="Aggressively prune unused PySide6 files from a onedir distribution."
    )
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
        sys.exit(0)

    print(f"Found {len(roots)} PySide6 tree(s):")
    for r in roots:
        print(" -", r)

    total_removed = []
    for r in roots:
        removed = prune_root(r, dry_run=args.dry_run)
        total_removed.extend(removed)

    if not total_removed:
        print("\nNo files matched the aggressive removal rules. Nothing to do.")
        return

    print(
        "\nThe following files would be removed:"
        if args.dry_run
        else "\nRemoved the following files:"
    )
    for p in total_removed:
        print(" -", p)

    if args.dry_run:
        print(f"\nDry-run complete. Would have removed {len(total_removed)} files.")
        print("Re-run without --dry-run to perform deletions.")
    else:
        print(f"\nPrune complete. Removed {len(total_removed)} files.")


if __name__ == "__main__":
    main()
