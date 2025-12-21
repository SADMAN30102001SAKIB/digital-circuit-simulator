# How to Build CircuitPlaygroundPro Executable

*(Note:)* For the smallest executable size, the project includes pre-configured **UPX folders** for Windows and Linux. On macOS, the script will automatically use the system-wide UPX (please install it via `brew install upx`).

## 🚀 Quick Start

Choose your build weapon:

| Method | Best For | Command |
| :--- | :--- | :--- |
| **Standard (PyInstaller)** | Fast testing & tiny executable sizes | `python build.py --spec-filter --exclude-qt` |
| **Compiler (Nuitka)** | Best RAM performance & security | `python nuitka_build.py --onefile` |

---

## 📦 Method 1: PyInstaller (Fast & Flexible)
This is the recommended way for most users.

### Option A: Using `uv` (Recommended 🚀)
1. **Install uv**:
   - **Windows (PowerShell)**:
     ```powershell
     powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - **Linux/macOS (Shell)**:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
2. **Setup environment**:
   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```
3. **Run build**:
    ```bash
    uv run build.py --spec-filter --exclude-qt
    ```

### Option B: Standard `venv`
1.  **Install dependencies**:
    ```bash
    sudo apt update
    sudo apt install python3-pip python3-venv
    ```
2.  **Create and activate**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Run Build**:
    ```bash
    python build.py --spec-filter --exclude-qt
    ```

### Find Output
`dist/CircuitPlaygroundPro`

> [!TIP]
> `uv` saves disk space by using a global cache and hard-linking packages across projects instead of copying them!

### 📋 Prerequisites (Linux & WSL2)
To run or build the Linux version, you **must** install the X11/Qt dependencies. These are required for the application to render graphics and handle window events.

**1. Graphical Dependencies:**
```bash
sudo apt update
sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-image0 libxcb-shm0 libxcb-render-util0 libxcb-xkb1 libxkbcommon-x11-0 libxcb-shape0 libxcb-util1
```

**2. Build Dependencies (Nuitka only):**
If you are using `nuitka_build.py` on Linux, you must install `patchelf` to allow the compiler to modify shared library paths in the standalone binary:
```bash
sudo apt install patchelf
```

### Onefile vs. Onedir: Which should you choose?

| Feature | `--onefile` (Default) | `--onedir` |
| :--- | :--- | :--- |
| **Output** | A single `CircuitPlaygroundPro` | A folder containing `CircuitPlaygroundPro` + `_internal` |
| **Startup Speed** | **Slower** (Unzips to temp folder) | **Instant** (Directly loads DLLs) |
| **Size** | **Smaller** (~22MB with filter) | **Larger** (~40MB with prune) |
| **Best For** | Casual sharing | Professional distribution |

**Tip:** 
- For the fastest startup: `python build.py --onedir --prune --exclude-qt`
- For an standalone executable: `python build.py --spec-filter --exclude-qt`

### 🔧 All Build Flags

| Flag | Description |
| :--- | :--- |
| `--name <NAME>` | Custom name for the output executable |
| `--onefile` | (Default) Compresses everything into a single executable |
| `--onedir` | Keeps dependencies in a separate folder for fast startup |
| `--prune` | (Onedir only) Deletes unused Qt translations and plugins |
| `--spec-filter` | Aggressive whitelist for minimum PySide6 binaries (~70% smaller) |
| `--exclude-qt` | Strips unused heavy modules (QML, WebEngine, etc.) |
| `--exclude-module <MOD>` | Exclude a specific Python package (e.g., `--exclude-module pygame`) |
| `--no-upx` | Disables UPX compression (Just for experimental purposes) |
| `--no-strip` | Disables binary symbol stripping (if the app crashes, the error message will say "Error in Button_Click" instead of "Error at 0x00452") |

### 🏆 The "Surgical Build" (Pro Mode)
If you want to hit the absolute minimum size (~21MB), you can surgically exclude "ghost" dependencies like `pygame` that might be sitting in your environment:
```powershell
python build.py --spec-filter --exclude-qt --exclude-module pygame
```

---

## 🧪 Method 2: Nuitka (The Pro Compiler)
Nuitka translates your Python code into C++ and compiles it into a native binary. This results in **25% less RAM usage** and faster execution.

### Setup (One-time):
1.  **Install**: `pip install nuitka zstandard` or `uv pip install nuitka zstandard`
> [!NOTE]
> Nuitka will ask to download a C++ compiler on the first run. Just say 'Yes'.

### Build Commands:
- **For a single executable**: `python nuitka_build.py --onefile`
- **For a folder**: `python nuitka_build.py --onedir`

---

## 📊 Benchmarks & Analysis
Want to see how we got down to ~21MB? Check out our full **[Size & Performance Report](BENCHMARKS.md)** for detailed data and analysis.

---

## 🛠️ Troubleshooting

*   **Antivirus Flags**: Single executables are sometimes flagged as "Unknown". This is a false positive. ZIP your executable for safer distribution.
*   **Slow Startup**: `--onefile` builds always unzip to a temp folder first. Use `--onedir` if you need instant startup on old hardware.

**📖 Full distribution tips: [DISTRIBUTION_FAQ.md](DISTRIBUTION_FAQ.md)**