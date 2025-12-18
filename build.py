import argparse
import subprocess
import sys
from pathlib import Path

import PyInstaller.__main__


def main(argv=None):
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
        default="Qt6Core,Qt6Gui,Qt6Widgets,Qt6Svg",
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
    args = parser.parse_args(argv)

    # Do not allow combining aggressive spec-filter workflow with conservative onedir pruning
    if args.spec_filter and args.onedir and args.prune:
        print(
            "Error: --spec-filter (aggressive spec-based build) cannot be combined with --onedir --prune (conservative onedir pruning)."
        )
        print(
            "Choose one of the following workflows:\n  python build.py --spec-filter [--exclude-qt]   # aggressive onefile\n  python build.py --onedir --prune               # conservative onedir + prune"
        )
        sys.exit(2)

    build_args = [
        "app.py",
        f"--name={args.name}",
        "--windowed",
        f"--icon={str(Path('assets/icon.ico').resolve())}",
        "--clean",
        "--noconfirm",
        "--strip",
        "--upx-dir=upx-5.0.2-win64",
        "--add-data=core;core",
        "--add-data=ui;ui",
        "--add-data=assets;assets",
    ]

    # If user requested spec-filter mode, generate a filtered spec that explicitly
    # allowlists the minimal PySide6 binaries and prunes the rest (this is the
    # aggressive approach that produced ~30MB onefile builds on Windows).
    if args.spec_filter:
        spec = Path("build") / f"{args.name}_filtered.spec"
        spec.parent.mkdir(parents=True, exist_ok=True)

        keep_qt = [x.strip().lower() for x in args.keep_qt_dlls.split(",") if x.strip()]

        # Probe PySide6 installation to locate DLLs and plugins
        try:
            import PySide6

            pyside_dir = Path(PySide6.__file__).parent
        except Exception:
            pyside_dir = None

        manual_bins = []
        if pyside_dir:
            # core Qt dlls
            for name in keep_qt:
                dll = pyside_dir / f"{name}.dll"
                if dll.exists():
                    manual_bins.append((str(dll), f"PySide6/{dll.name}"))

            # (skip adding runtime/support DLLs here to keep the allowlist minimal)

            # minimal plugins we want to keep (platform + only qico to avoid bringing QtSvg)
            for folder, names in [
                ("platforms", ["qwindows"]),
                ("imageformats", ["qico"]),
            ]:
                for nm in names:
                    p = pyside_dir / "plugins" / folder / (nm + ".dll")
                    if p.exists():
                        manual_bins.append(
                            (str(p), f"PySide6/plugins/{folder}/{p.name}")
                        )

        # Build the .spec contents (explicit binaries list and optional excludes)
        excludes = []
        exclude_qt_flag = False
        if args.exclude_qt:
            exclude_qt_flag = True
            excludes = [
                "PySide6.QtQml",
                "PySide6.QtQuick",
                "PySide6.QtPdf",
                "PySide6.QtQmlModels",
                "PySide6.QtQuickControls2",
                "PySide6.QtQuickWidgets",
                "PySide6.QtWebEngineCore",
                "PySide6.QtWebEngineWidgets",
            ]

        excludes_literal = "[" + ", ".join(f'r"{e}"' for e in excludes) + "]"

        lines = []
        lines.append(f"exclude_qt_flag = {str(exclude_qt_flag)}")
        lines.append("# -*- mode: python ; coding: utf-8 -*-")
        lines.append("block_cipher = None")
        lines.append("")
        main_path_val = str(Path.cwd() / "app.py").replace("\\\\", "/")
        project_root_val = str(Path.cwd()).replace("\\\\", "/")
        lines.append(f'main_path = r"{main_path_val}"')
        lines.append(f'project_root = r"{project_root_val}"')
        lines.append("")

        lines.append("binaries = [")
        for src, dst in manual_bins:
            safe_src = src.replace("\\\\", "/")
            dst_safe = dst.replace("\\\\", "/")
            lines.append(f'    (r"{dst_safe}", r"{safe_src}", \'b\'),')
        lines.append("]")
        lines.append("")
        lines.append(
            "datas = [ (project_root + '/core','core'), (project_root + '/ui','ui'), (project_root + '/assets','assets') ]"
        )
        lines.append("")
        lines.append(
            f"a = Analysis([main_path], pathex=[project_root], binaries=[], datas=datas, hiddenimports=[], hookspath=['hooks'], excludes={excludes_literal}, runtime_hooks=[], win_no_prefer_redirects=False, win_private_assemblies=False, cipher=block_cipher)"
        )
        lines.append("")
        lines.append(
            "# Aggressive post-analysis filtering: remove Qt module files by name fragments when requested"
        )
        lines.append(
            "print('Pre-filter PySide6 entries in a.binaries:', [b[1].replace('\\\\','/') for b in a.binaries if b[1].replace('\\\\','/').startswith('PySide6/')])"
        )
        lines.append("allowed = {")
        for _, dst in manual_bins:
            dst_safe2 = dst.replace("\\\\", "/")
            lines.append(f'    r"{dst_safe2}",')
        lines.append("}")
        lines.append("if exclude_qt_flag:")
        lines.append(
            "    ex_cl = ['qt6qml','qt6qmlmeta','qt6qmlmodels','qt6qmlworkerscript','qt6quick','qt6pdf','qt6webengine','qt6webenginecore','qt6svg','qsvg','qt6network','qt6opengl','qt6virtualkeyboard','qt6multimedia','qt6webchannel','qt6websockets','opengl32sw','qjpeg','qwebp','libcrypto-3','libcrypto','libssl','qtjpeg','qtwebp']"
        )
        lines.append(
            "    a.binaries = [b for b in a.binaries if not any(x in b[1].replace('\\\\','/').lower() for x in ex_cl)]"
        )
        lines.append(
            "a.binaries = [b for b in a.binaries if ((b[1].replace('\\\\','/')) in allowed) or (not (b[1].replace('\\\\','/')).startswith('PySide6/'))]"
        )
        lines.append("print('--- Binary filter keeps', len(a.binaries), 'entries')")
        lines.append(
            "print('Kept (dest) =', [b[1].replace('\\\\','/') for b in a.binaries if b[1].replace('\\\\','/').startswith('PySide6/')])"
        )
        lines.append("")
        lines.append("pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)")
        strip_flag = "True" if args.strip else "False"
        lines.append(
            f"exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, name='{args.name}', debug=False, strip={strip_flag}, upx=True, console=False, icon=r\"{project_root_val}/assets/icon.ico\")"
        )

        spec_text = "\n".join(lines) + "\n"
        spec.write_text(spec_text)
        print(f"Wrote filtered spec to {spec}")

        # Remove PyInstaller bincache to avoid PermissionError collisions on Windows
        import shutil

        bincache_root = Path.home() / "AppData" / "Local" / "pyinstaller"
        if bincache_root.exists():
            try:
                shutil.rmtree(bincache_root)
                print(f"Removed PyInstaller bincache at {bincache_root}")
            except Exception:
                print(f"Warning: failed to remove bincache at {bincache_root}")

        PyInstaller.__main__.run([str(spec)])
        return

    print("Running PyInstaller with:", " ".join(build_args))
    PyInstaller.__main__.run(build_args)

    dist_path = Path("dist") / args.name
    if args.onedir and args.prune:
        prune_script = Path(__file__).parent / "scripts" / "prune.py"
        if prune_script.exists():
            print(f"Running prune script on {dist_path}")
            subprocess.check_call(["python", str(prune_script), str(dist_path)])
            print("✅ Prune complete.")
        else:
            print("⚠️ Prune script not found, skipping")

    print(
        "\n✅ Build complete! Check dist/"
        + args.name
        + (" (onedir)" if args.onedir else ".exe (onefile)")
    )


if __name__ == "__main__":
    main()
