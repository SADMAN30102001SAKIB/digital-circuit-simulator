import argparse
import subprocess
import sys
from pathlib import Path

def check_nuitka():
    try:
        subprocess.run([sys.executable, "-m", "nuitka", "--version"], capture_output=True, check=True)
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
        "--onefile", action="store_true", help="Build a single executable (requires Zstandard)"
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
        sys.executable, "-m", "nuitka",
        "--standalone",  # Always start with standalone
        f"--output-filename={args.name}",
        "--enable-plugin=pyside6",
        "--remove-output", # Clean up the build folder after success
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
        cmd.append(f"--include-data-dir=assets=assets")

    # Entry Point
    cmd.append("app.py")

    print("🚀 Starting Experimental Nuitka Build...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.check_call(cmd)
        print(f"\n✅ Build complete! Check app.dist (or the executable in project root if onefile)")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Nuitka build failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
