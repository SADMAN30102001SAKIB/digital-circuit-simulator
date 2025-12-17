# How to Build CircuitPlaygroundPro.exe

⚠️ **Note:** This build process is for **Windows only**. For Linux/Mac, run the Python source directly.

## Prerequisites

```powershell
pip install pyinstaller
```

## Build Command

```powershell
python build.py
```

## Output

- Executable: `dist/CircuitPlaygroundPro.exe`
- Build files: `build/` folder (can be deleted)
- Spec file: `CircuitPlaygroundPro.spec` (PyInstaller config)

## Build Time

Approximately 1-2 minutes on modern hardware

## Distribution

Just distribute the single .exe file from the `dist/` folder.
No other files needed!

**📖 For complete distribution details, see [EXE_DISTRIBUTION_FAQ.md](EXE_DISTRIBUTION_FAQ.md)**

## Customization Options

### Add Icon

1. Create/find a .ico file & name it `icon.ico`
2. Replace the existing `icon.ico` in `assets/` folder & `build.py` will automatically include it

### Flagged builds

Example (aggressive build):

```powershell
python build.py --spec-filter --exclude-qt
```

Example (conservative onedir + prune):

```powershell
python build.py --onedir --prune
```

## All Flags (quick reference) 🔧

### Usage:

```powershell
python build.py [options]
```

### Flags:

- `--name <NAME>`

  - Set the output name for the EXE or the onedir (example: `--name OnefileUltraAggressive`).

- `--onefile` (default)

  - Build a single-file executable (onefile).

- `--onedir`

  - Build an onedir distribution (folder containing the exe and its dependencies).

- `--prune`

  - When used with `--onedir`, run the conservative PySide6 prune script to remove unnecessary plugins and translations.

- `--spec-filter`

  - Generate and use a filtered `.spec` that explicitly allowlists a minimal set of PySide6 binaries/plugins and performs a post-analysis prune for aggressive size reduction.

- `--exclude-qt`

  - Use together with `--spec-filter` to drop common Qt modules (QML / Quick / PDF / WebEngine and related fragments) from the final bundle.

- `--keep-qt-dlls <LIST>`

  - Comma-separated list of Qt DLL basenames to keep when building the filtered spec (default: `Qt6Core,Qt6Gui,Qt6Widgets,Qt6Svg`).

- `--no-strip`

  - Disable `strip` for binaries when using the generated spec (useful if `strip` fails on Windows).

- `-h `, `--help`

  - Show help message and exit.

## Troubleshooting

### Build Fails

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Clear cache: Delete `build/` and `dist/` folders, then rebuild

### Antivirus False Positive

- PyInstaller executables are commonly flagged
- Add exception or code-sign the .exe (requires certificate)

### Missing DLL Warnings

- Warnings about fbclient.dll, OCI.dll etc. are normal
- These are optional SQL drivers not used by the app
