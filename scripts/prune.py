import shutil
import sys
from pathlib import Path

# Identify Platform
IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform.startswith("darwin")
IS_LINUX = sys.platform.startswith("linux")

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
    "python",  # Core Python binary on Mac/Linux
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
    "opengl32sw",
    "qjpeg",
    "qwebp",
    "libcrypto",
    "libssl",
    "qtjpeg",
    "qtwebp",
    "qtiff",
    "qicns",
    "qwbmp",
    "qtga",
    "qgif",
    "qdirect2d",
    "virtualkeyboard",
    "opengl",
    "webview",
    "meta",
    "workerscript",
    "models",
    "serialbus",
    "3d",
    "concurrent",
    "printsupport",
    "qtxml",
    "texttospeech",
    "location",
    # Cross-platform safety net (Linux-only plugins on Windows/Mac)
    "qwayland",
    "qeglfs",
    "qlinuxfb",
    "qvnc",
]

# System-specific allowed plugins (use BASE NAMES for cross-platform matching)
PLATFORM_PLUGIN = "qwindows" if IS_WIN else ("qcocoa" if IS_MAC else "qxcb")
STYLE_PLUGIN = "qwindowsvistastyle" if IS_WIN else ("qmacstyle" if IS_MAC else None)

# Use base names without extensions for robust cross-platform matching
# Matching is done via substring, so "qico" will match "qico.dll", "libqico.so.6", etc.
ALLOW_PLUGINS = {
    "platforms": {PLATFORM_PLUGIN},
    "imageformats": {"qico", "qpng"},
}
if STYLE_PLUGIN:
    ALLOW_PLUGINS["styles"] = {STYLE_PLUGIN}

KEEP_TRANSLATIONS = {"qt_en.qm", "qt_help_en.qm"}


def find_pyside_roots(dist_path: Path):
    roots = []
    # 1. Look for the main _internal folder (Standard for newer PyInstaller)
    # On Mac, this is often deep inside Contents/MacOS/
    for p in dist_path.rglob("_internal"):
        if p.is_dir() and p not in roots:
            roots.append(p)

    # 2. Look for any explicit PySide6 folders (Sometimes in root or _internal)
    for p in dist_path.rglob("PySide6"):
        if p.is_dir() and p not in roots:
            # Avoid adding subfolders of already added roots
            if not any(r in p.parents for r in roots):
                roots.append(p)

    # 3. Look in Frameworks and Resources (Typical for bundles)
    for folder_name in ["Frameworks", "Resources"]:
        for p in dist_path.rglob(folder_name):
            if p.is_dir() and p not in roots:
                # Avoid adding subfolders of already added roots
                if not any(r in p.parents for r in roots):
                    roots.append(p)

    return roots


def prune_root(root: Path, dry_run: bool = True):
    removed = []

    # 1. Prune binaries (Aggressive & Recursive)
    # Search for ALL binary extensions regardless of host OS
    # On Mac, some binaries have NO extension (e.g. 'QtGui', 'QtPdf')
    for dll in root.rglob("*"):
        if dll.is_dir():
            continue  # Skip directories in this pass

        dll_name = dll.name.lower()

        # We only want to prune libraries/binaries.
        # Skip files that have extensions we DON'T want to prune here (like .py, .txt, .qm)
        if dll.suffix and dll.suffix.lower() not in [".dylib", ".so", ".dll", ".pyd"]:
            # On Mac/Linux, we might have libX.so.6 - we want to keep/check those too
            if not (".so." in dll_name or ".dylib." in dll_name):
                continue

        # Extensionless files are only pruned on non-Windows logic or if they look like Qt libs
        if not dll.suffix:
            # If it doesn't look like a Mac binary or high-risk fragment, skip it
            if not any(
                frag in dll_name for frag in UNNEEDED_DLL_FRAGMENTS
            ) and not dll_name.startswith("qt"):
                continue

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

    # 2. Prune Plugins (Conservative & Recursive Search for Folder)
    # On Mac/Linux, plugins might be in PySide6/Qt/plugins/
    for plugins_dir in root.rglob("plugins"):
        if not plugins_dir.is_dir():
            continue

        for folder in plugins_dir.iterdir():
            if not folder.is_dir():
                continue

            folder_name = folder.name.lower()

            # If the category is allowed, we might still prune INSIDE it
            if folder_name in ALLOW_PLUGINS:
                allowed_files = ALLOW_PLUGINS[folder_name]
                for file in folder.iterdir():
                    if file.is_dir():
                        continue
                    # Keep if it matches a whitelisted file (handle lib prefix or versioning)
                    file_name = file.name.lower()
                    if any(whitelisted in file_name for whitelisted in allowed_files):
                        continue

                    # Otherwise, it's a ghost inside an allowed folder
                    removed.append(file)
                    if not dry_run:
                        try:
                            file.unlink()
                        except Exception as e:
                            print(f"Warning: failed to remove {file}: {e}")
                continue

            # Otherwise, it's an unused category (like 'qml' or 'multimedia' plugins)
            removed.append(folder)
            if not dry_run:
                try:
                    shutil.rmtree(folder)
                except Exception as e:
                    print(f"Warning: failed to remove {folder}: {e}")

    # 3. Prune Translations (Recursive Search for Folder)
    # On Mac/Linux, translations might be in PySide6/Qt/translations/
    for trans_dir in root.rglob("translations"):
        if not trans_dir.is_dir():
            continue

        for qm in trans_dir.rglob("*.qm"):
            if qm.name in KEEP_TRANSLATIONS:
                continue
            removed.append(qm)
            if not dry_run:
                try:
                    qm.unlink()
                except Exception as e:
                    print(f"Warning: failed to remove {qm}: {e}")

    # 4. Prune Mac Frameworks (Mac Specific)
    if IS_MAC:
        # Frameworks on Mac are directories ending in .framework
        for fw in root.rglob("*.framework"):
            fw_name = fw.name.lower()
            # Protect core frameworks
            if any(core in fw_name for core in REQUIRED_CORES):
                continue
            # Remove if it matches unneeded fragments
            if any(frag in fw_name for frag in UNNEEDED_DLL_FRAGMENTS):
                removed.append(fw)
                if not dry_run:
                    try:
                        shutil.rmtree(fw)
                    except Exception as e:
                        print(f"Warning: failed to remove {fw}: {e}")

    return removed


def main():
    import argparse

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

    # Dynamic Protection: Protect the main app binary itself
    target_app_name = dist_path.stem.lower()
    REQUIRED_CORES.add(target_app_name)

    print(f"Found {len(roots)} PySide6/Bundle tree(s):")
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
