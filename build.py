import argparse
import subprocess
import sys
from pathlib import Path

import PyInstaller.__main__
import os
import platform

# Identify Platform
IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform.startswith("darwin")
IS_LINUX = sys.platform.startswith("linux")

# Dynamic Constants
SEP = ";" if IS_WIN else ":"
EXT = ".dll" if IS_WIN else (".dylib" if IS_MAC else ".so")


def check_linux_dependencies():
    """Check for common Linux libraries that PySide6/Qt needs for X11."""
    if IS_WIN or platform.system() == 'Darwin': return
    
    needed = [
        'libxcb-cursor.so.0', 'libxcb-icccm.so.4', 'libxcb-keysyms.so.1',
        'libxcb-image.so.0', 'libxcb-shm.so.0', 'libxcb-render-util.so.0',
        'libxcb-xkb.so.1', 'libxkbcommon-x11.so.0', 'libxcb-shape.so.0',
        'libxcb-util.so.1'
    ]
    missing = []
    
    import shutil
    import subprocess
    try:
        # Try using ldconfig to see if they are in the cache
        ld_output = subprocess.check_output(['ldconfig', '-p'], stderr=subprocess.STDOUT).decode()
        for lib in needed:
            if lib not in ld_output:
                missing.append(lib)
    except:
        # Fallback to shutil check if ldconfig fails
        for lib in needed:
            if not shutil.which(lib): missing.append(lib)

    if missing:
        print("\n\033[93m⚠️  Warning: Missing Linux GUI dependencies on build machine!\033[0m")
        print("Without these, your Linux executable might not run on other systems.")
        print("Run this to fix: \033[96msudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-image0 libxcb-shm0 libxcb-render-util0 libxcb-xkb1 libxkbcommon-x11-0 libxcb-shape0 libxcb-util1\033[0m")
        print("-" * 50 + "\n")


def main(argv=None):
    check_linux_dependencies()
    parser = argparse.ArgumentParser(
        description="Build CircuitPlaygroundPro with optional filtered spec for small onefile builds"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--onefile", action="store_true", help="Build a onefile executable (default)"
    )
    group.add_argument(
        "--onedir", action="store_true", help="Build a onedir distribution"
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Run post-build pruning (works on --onedir output)",
    )
    parser.add_argument(
        "--name", default="CircuitPlaygroundPro", help="Executable name"
    )
    parser.add_argument(
        "--spec-filter",
        action="store_true",
        help="Generate and use a filtered spec that removes unneeded PySide6 binaries/plugins (aggressive)",
    )
    parser.add_argument(
        "--keep-qt-dlls",
        default="Qt6Core,Qt6Gui,Qt6Widgets,Qt6DBus",
        help="Comma-separated Qt DLL names to keep (no .dll suffix)",
    )
    parser.add_argument(
        "--no-strip",
        dest="strip",
        action="store_false",
        help="Do not strip binaries when using the generated spec",
    )
    parser.add_argument(
        "--exclude-qt",
        dest="exclude_qt",
        action="store_true",
        help="Exclude common QML/Quick/PDF/WebEngine PySide6 modules in generated spec (experimental)",
    )
    parser.add_argument(
        "--no-upx",
        action="store_true",
        help="Disable UPX compression for all build artifacts",
    )
    parser.add_argument(
        "--exclude-module",
        action="append",
        default=[],
        help="Exclude a specific Python module from the build (e.g., --exclude-module pygame)",
    )
    args = parser.parse_args(argv)

    # Validation: --prune only works on directories
    if args.prune and not args.onedir:
        print("Error: --prune can only be used with --onedir builds.")
        print("Pruning is a post-processing step that removes files from a directory. It cannot be performed on a single executable.")
        sys.exit(2)

    # Validation: --exclude-qt is most effective with --spec-filter or --onedir
    if args.exclude_qt and not (args.spec_filter or args.onedir):
        print("Tip: --exclude-qt is currently most effective when combined with --spec-filter or --onedir --prune.")

    build_args = [
        "app.py",
        f"--name={args.name}",
        "--windowed",
        "--clean",
        "--noconfirm",
        "--strip",
        f"--add-data=core{SEP}core",
        f"--add-data=ui{SEP}ui",
        f"--add-data=assets{SEP}assets",
    ]

    # Handle Icon
    icon_ext = ".ico" if not IS_MAC else ".icns"
    icon_path = Path("assets") / f"icon{icon_ext}"
    if icon_path.exists():
        build_args.append(f"--icon={str(icon_path.resolve())}")

    # Smarter UPX Detection
    upx_found = False
    if not args.no_upx:
        # Search for any upx folder in root
        for p in Path(".").iterdir():
            if p.is_dir() and "upx" in p.name.lower():
                # Check for platform match or generic
                if (IS_WIN and "win" in p.name.lower()) or \
                   (IS_LINUX and "linux" in p.name.lower()):
                    # Note: On Mac, it's best to 'brew install upx'. 
                    # This check is for power users who place a compiled upx binary in 'upx-mac'.
                    build_args.append(f"--upx-dir={p.name}")
                    print(f"✅ Using UPX from: {p.name}")
                    upx_found = True
                    break
        
        if not upx_found:
             # If no folder, PyInstaller will still check system PATH
             pass
    else:
        build_args.append("--noupx")

    # Standard exclusions if exclude-qt is requested (global)
    if args.exclude_qt:
        for mod in [
            "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtPdf",
            "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
            "PySide6.QtNetwork", "PySide6.QtBluetooth", "PySide6.QtMultimedia",
            "PySide6.QtSvg", "PySide6.QtSvgWidgets",
            "unittest", "pydoc", "email", "http", "xml", "html", "distutils", "setuptools"
        ]:
            build_args.extend(["--exclude-module", mod])

    # Handle onefile vs onedir
    if args.onedir:
        build_args.append("--onedir")
    else:
        build_args.append("--onefile")

    # Handle explicit module exclusions
    for mod in args.exclude_module:
        build_args.extend(["--exclude-module", mod])

    if args.spec_filter:
        spec = Path("build") / f"{args.name}_filtered.spec"
        spec.parent.mkdir(parents=True, exist_ok=True)

        keep_qt = [x.strip().lower() for x in args.keep_qt_dlls.split(",") if x.strip()]

        try:
            import PySide6
            pyside_dir = Path(PySide6.__file__).parent
        except Exception:
            pyside_dir = None

        manual_bins = []
        if pyside_dir:
            # Keep essential plugins (Platform specific)
            platform_plugin = "qwindows" if IS_WIN else ("qcocoa" if IS_MAC else "qxcb")
            style_plugin = "qwindowsvistastyle" if IS_WIN else ("qmacstyle" if IS_MAC else None)
            
            plugin_map = [
                ("platforms", [platform_plugin]),
            ]
            if style_plugin:
                plugin_map.append(("styles", [style_plugin]))

            for folder, names in plugin_map:
                for nm in names:
                    # Glob to catch qxcb.dll or libqxcb.so or libqxcb.so.6
                    patterns = [f"{nm}{EXT}", f"lib{nm}{EXT}*", f"{nm}{EXT}*"]
                    for pat in patterns:
                        for p in (pyside_dir / "plugins" / folder).glob(pat):
                            if p.is_file():
                                manual_bins.append((str(p), f"PySide6/plugins/{folder}/{p.name}"))
                                break

        excludes = []
        if args.exclude_qt:
            excludes = [
                "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtPdf",
                "PySide6.QtQmlModels", "PySide6.QtQuickControls2",
                "PySide6.QtWebEngineCore", "PySide6.QtNetwork",
                "PySide6.QtSvg", "PySide6.QtSvgWidgets",
                "unittest", "pydoc", "email", "http", "xml", "html"
            ]
        
        # Add user-requested exclusions to the spec
        if args.exclude_module:
            excludes.extend(args.exclude_module)

        excludes_literal = "[" + ", ".join(f'r"{e}"' for e in excludes) + "]"

        # Unified path joining for Spec
        main_path_val = str(Path.cwd() / "app.py").replace("\\", "/")
        project_root_val = str(Path.cwd()).replace("\\", "/")
        lines = [
            f"exclude_qt_flag = {str(args.exclude_qt)}",
            "# -*- mode: python ; coding: utf-8 -*-",
            "block_cipher = None",
            "",
            f'main_path = r"{main_path_val}"',
            f'project_root = r"{project_root_val}"',
            "",
            "allowed_pyside = ["
        ]
        for src, dst in manual_bins:
            src_safe = src.replace("\\", "/")
            dst_safe = dst.replace("\\", "/")
            lines.append(f'    r"{dst_safe}",')
        lines.append("]")
        lines.append("")
        lines.append(f"datas = [ (project_root + '/core','core'), (project_root + '/ui','ui'), (project_root + '/assets','assets') ]")
        lines.append("")
        win_flags = "win_no_prefer_redirects=False, win_private_assemblies=False, " if IS_WIN else ""
        lines.append(f"a = Analysis([main_path], pathex=[project_root], binaries=[], datas=datas, hiddenimports=[], hookspath=[], excludes={excludes_literal}, runtime_hooks=[], {win_flags}cipher=block_cipher)")
        lines.append("")
        lines.append("# Aggressive post-analysis filtering")
        lines.append("if exclude_qt_flag:")
        lines.append("    ex_cl = ['qt6qml','qt6qmlmeta','qt6qmlmodels','qt6qmlworkerscript','qt6quick','qt6pdf','qt6webengine','qt6webenginecore','qt6svg','qsvg','qt6network','qt6opengl','qt6virtualkeyboard','qt6multimedia','qt6webchannel','qt6websockets','opengl32sw','qjpeg','qwebp','libcrypto-3','libcrypto','libssl','qtjpeg','qtwebp','qtiff','qicns','qwbmp','qtga','qgif','qminimal','qoffscreen','qdirect2d']")
        lines.append("    a.binaries = [b for b in a.binaries if not any(x in b[1].lower() for x in ex_cl)]")
        lines.append("")
        lines.append("# Keep ONLY the PySide6 files we explicitly allowed, plus non-PySide6 dependencies")
        lines.append("def is_allowed_pyside(name):")
        lines.append("    n = name.replace('\\\\','/').lower()")
        lines.append("    # Always keep core Qt libraries on Linux (they have complex symlinks)")
        lines.append(f"    if not {IS_WIN} and ('pyside6/qt' in n or 'pyside6/Qt' in name): return True")
        lines.append("    # Core libs and plugins across all platforms")
        lines.append("    if not 'pyside6' in n and not 'plugins' in n: return True")
        lines.append("    # Keep ONLY essential plugins")
        lines.append("    if n in [x.lower() for x in allowed_pyside]: return True")
        lines.append("    # Explicit Whitelist for standard logic")
        lines.append("    for plugin in ['plugins/platforms/', 'plugins/imageformats/qico', 'plugins/styles/']:")
        lines.append("        if plugin in n: return True")
        lines.append("    # Core modules and extensions that MUST stay")
        lines.append("    base = n.split('/')[-1]")
        lines.append("    for core in ['qt6core', 'qt6gui', 'qt6widgets', 'qt6dbus', 'qtcore', 'qtgui', 'qtwidgets', 'qtdbus', 'pyside6', 'shiboken6']:")
        lines.append("        if core in base: return True")
        lines.append("    return False")
        lines.append("a.binaries = [b for b in a.binaries if is_allowed_pyside(b[0])]")
        lines.append("")
        lines.append("pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)")
        strip_flag = "True" if args.strip else "False"
        upx_flag = "False" if args.no_upx else "True"
        
        if args.onedir:
            lines.append(f"exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='{args.name}', debug=False, strip={strip_flag}, upx={upx_flag}, console=False, icon=r'{project_root_val}/assets/icon{icon_ext}')")
            lines.append(f"coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip={strip_flag}, upx={upx_flag}, name='{args.name}')")
        else:
            lines.append(f"exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, name='{args.name}', debug=False, strip={strip_flag}, upx={upx_flag}, console=False, icon=r'{project_root_val}/assets/icon{icon_ext}')")

        spec.write_text("\n".join(lines) + "\n")
        print(f"Wrote filtered spec to {spec}")

        run_args = [str(spec)]
        if not args.no_upx and upx_found:
            for p in Path(".").iterdir():
                if p.is_dir() and "upx" in p.name.lower():
                     if (IS_WIN and "win" in p.name.lower()) or \
                        (IS_LINUX and "linux" in p.name.lower()) or \
                        (IS_MAC and "mac" in p.name.lower()):
                         run_args.extend(["--upx-dir", p.name])
                         break
        PyInstaller.__main__.run(run_args)
    else:
        print("Running PyInstaller...")
        PyInstaller.__main__.run(build_args)

    # Post-build pruning (only for directory builds)
    dist_path = Path("dist") / args.name
    if args.onedir and args.prune:
        prune_script = Path(__file__).parent / "scripts" / "prune.py"
        if prune_script.exists():
            print(f"Running prune script on {dist_path}")
            subprocess.check_call([sys.executable, str(prune_script), str(dist_path)])
            print("✅ Prune complete.")

    print(f"\n✅ Build complete! Check dist/{args.name}")

if __name__ == "__main__":
    main()
