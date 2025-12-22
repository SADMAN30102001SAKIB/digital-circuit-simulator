import argparse
import subprocess
import sys
from pathlib import Path


def check_nuitka():
    try:
        subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_patchelf():
    try:
        subprocess.run(["patchelf", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Experimental Nuitka Build Script for CircuitPlaygroundPro"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--onefile",
        action="store_true",
        help="Build a single executable (requires Zstandard)",
    )
    group.add_argument(
        "--onedir", action="store_true", help="Build a standalone directory (default)"
    )
    parser.add_argument(
        "--name", default="CircuitPlaygroundPro", help="Executable name"
    )
    args = parser.parse_args(argv)

    if not check_nuitka():
        print("Error: Nuitka is not installed in your Python environment.")
        print("\nTo install Nuitka and its dependencies, run:")
        print("pip install -U nuitka zstandard")
        sys.exit(1)

    # Platform Detection
    is_win = sys.platform.startswith("win")
    is_mac = sys.platform.startswith("darwin")
    is_linux = sys.platform.startswith("linux")

    if is_linux and not check_patchelf():
        print("Error: 'patchelf' is not installed.")
        print("\nStandalone mode on Linux requires 'patchelf'. Install it with:")
        print("sudo apt install patchelf")
        sys.exit(1)

    # Base Nuitka Command
    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",  # Always start with standalone
        f"--output-filename={args.name}",
        "--enable-plugin=pyside6",
        "--remove-output",  # Clean up the build folder after success
        "--assume-yes-for-downloads",  # Automatic download of dependencies in CI
    ]

    # Handle Windows Specifics
    if is_win:
        cmd.append("--windows-icon-from-ico=assets/icon.ico")
        cmd.append("--windows-console-mode=disable")

    # Handle Mac Specifics
    if is_mac:
        if Path("assets/icon.icns").exists():
            cmd.append("--macos-app-icon=assets/icon.icns")
        cmd.append("--macos-create-app-bundle")

    # Handle Onefile
    if args.onefile:
        cmd.append("--onefile")

    # Include Data Folders (Non-Python assets)
    if Path("assets").exists():
        cmd.append("--include-data-dir=assets=assets")

    # Entry Point
    cmd.append("app.py")

    print("[BUILD] Starting Nuitka Build...")
    print(f"Command: {' '.join(cmd)}\n")

    try:
        subprocess.check_call(cmd)

        # Post-build renaming
        # Nuitka defaults to 'app.dist' or 'app.app' because the script is 'app.py'
        # We need to rename these to the user-specified name so the release script finds them.
        import shutil
        import time

        # We check for both .dist (Linux/Win/Mac) and .app (Mac)
        extensions = [".dist", ".app"]
        if is_win and args.onefile:
            # On Windows onefile, Nuitka creates {args.name}.exe directly if --output-filename is used
            # but sometimes it might still be app.exe if flags are wonky.
            extensions.append(".exe")
        elif (is_linux or is_mac) and args.onefile:
            # On Unix onefile, it might be {args.name} or {args.name}.bin
            extensions.append(".bin")
            extensions.append("")  # No extension

        for ext in extensions:
            # We look for 'app' prefix as it's the script name
            default_path = Path(f"app{ext}")
            target_path = Path(f"{args.name}{ext}")

            if default_path.exists() and default_path != target_path:
                if target_path.exists():
                    if target_path.is_dir():
                        shutil.rmtree(target_path)
                    else:
                        target_path.unlink()

                print(f"[INFO] Renaming {default_path} to {target_path}...")
                for i in range(5):
                    try:
                        default_path.rename(target_path)
                        print(f"[INFO] Successfully renamed to {target_path}")
                        break
                    except (PermissionError, OSError) as e:
                        if i == 4:
                            print(f"[WARNING] Could not rename {default_path}: {e}")
                        else:
                            time.sleep(1)

        # Mac-specific Onefile "Rescue Bundle" logic
        if is_mac and args.onefile:
            # Nuitka --onefile --macos-create-app-bundle often produces just a binary file 'app' or '{name}'.
            # We check if a bundle folder actually exists.
            bundle_path = Path(f"{args.name}.app")
            binary_path = Path(args.name)

            if (
                not bundle_path.exists()
                and binary_path.exists()
                and binary_path.is_file()
            ):
                print(f"[INFO] Wrapping {args.name} into a professional .app bundle...")
                macos_dir = bundle_path / "Contents" / "MacOS"
                resources_dir = bundle_path / "Contents" / "Resources"
                macos_dir.mkdir(parents=True, exist_ok=True)
                resources_dir.mkdir(parents=True, exist_ok=True)

                # Move binary
                shutil.move(str(binary_path), str(macos_dir / args.name))

                # Add Icon if available
                icon_source = Path("assets/icon.icns")
                if icon_source.exists():
                    shutil.copy(str(icon_source), str(resources_dir / "icon.icns"))

                # Create minimal Info.plist
                plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>{args.name}</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.circuit-simulator.{args.name.lower()}</string>
    <key>CFBundleName</key>
    <string>{args.name}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>3.1.3</string>
</dict>
</plist>
"""
                with open(bundle_path / "Contents" / "Info.plist", "w") as f:
                    f.write(plist_content)

                print(f"[SUCCESS] Hand-crafted .app bundle created at {bundle_path}")

        # Ad-hoc Code Signing (Mac only)
        if is_mac:
            bundle_path = Path(f"{args.name}.app")
            if bundle_path.exists() and bundle_path.is_dir():
                print(f"[INFO] Applying ad-hoc code signature to {bundle_path}...")
                try:
                    subprocess.run(
                        [
                            "codesign",
                            "--force",
                            "--deep",
                            "--sign",
                            "-",
                            str(bundle_path),
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    print(
                        f"[SUCCESS] Ad-hoc signature applied. '_CodeSignature' folder generated."
                    )
                except subprocess.CalledProcessError as e:
                    print(f"[WARNING] Ad-hoc signing failed: {e.stderr}")
                except FileNotFoundError:
                    print(
                        f"[WARNING] 'codesign' utility not found. Skipping signature."
                    )

        print(f"\n[SUCCESS] Build complete! Artifact name: {args.name}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Nuitka build failed with exit code {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
