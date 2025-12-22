# How to Build CircuitPlaygroundPro Executable

*(Note:)* For the smallest executable size, the project includes pre-configured **UPX folders** for Windows and Linux. 
On macOS, the script will automatically use the system-wide UPX (please install it via `brew install upx`).

## 🚀 Quick Start

Choose your build weapon:

| Method | Best For |
| :--- | :--- |
| **Standard (PyInstaller)** | Fast testing & smallest build sizes |
| **Compiler (Nuitka)** | Best RAM performance & security |

### 📋 Prerequisites (Linux & WSL2)

**Build Dependencies (Nuitka only):**
If you are using `nuitka_build.py` on Linux, you must install `patchelf` to allow the compiler to modify shared library paths in the standalone binary:
```bash
sudo apt install patchelf
```

---

## 📦 Method 1: PyInstaller (Fast & Flexible)
This is the recommended way for most users.

### Option A: Using `uv` (Recommended 🚀)
1. **Run build** (auto-installs build dependencies):
    ```bash
    uv run --extra build build.py --spec-filter --exclude-qt
    ```

### Option B: Standard `pip`
1. **Create and activate virtual environment**:
    ```bash
    # Windows: 
    python -m venv .venv
    .venv\Scripts\activate

    # Linux/macOS:
    sudo apt install python3-venv
    python3 -m venv .venv
    source .venv/bin/activate
    ```
2. **Install build dependencies**:
    ```bash
    pip install .[build]
    ```
3. **Run Build**:
    ```bash
    python build.py --spec-filter --exclude-qt
    ```

> [!TIP]
> `uv` saves disk space by using a global cache and hard-linking packages across projects instead of copying them!

### Onefile vs. Onedir: Which should you choose?

| Feature | `--onefile` (Default) | `--onedir` |
| :--- | :--- | :--- |
| **Output** | A single `CircuitPlaygroundPro` | A folder containing `CircuitPlaygroundPro` + `_internal` |
| **Startup Speed** | **Slower** (Unzips to temp folder) | **Instant** (Directly loads DLLs) |
| **Size** | **Smaller** | **Larger** |
| **Best For** | Casual sharing | Professional distribution |

**Tip:** 
- For the fastest startup: `uv run --extra build build.py --onedir --prune --exclude-qt`
- For standalone executable: `uv run --extra build build.py --spec-filter --exclude-qt`

### 🔧 All Build Flags

| Flag | Description |
| :--- | :--- |
| `--name "NAME"` | Custom name for the output executable |
| `--onefile` | (Default) Compresses everything into a single executable |
| `--onedir` | Keeps dependencies in a separate folder for fast startup |
| `--prune` | (Onedir only) Deletes unused Qt translations and plugins |
| `--spec-filter` | Aggressive whitelist for minimum PySide6 binaries (~70% smaller) |
| `--exclude-qt` | Strips unused heavy modules (QML, WebEngine, etc.) |
| `--exclude-module <MOD>` | Exclude a specific Python package (e.g., `--exclude-module pygame`) |
| `--no-upx` | Disables UPX compression |
| `--no-strip` | Disables binary symbol stripping (if the app crashes, the error message will say "Error in Button_Click" instead of "Error at 0x00452") |

### 🏆 The "Surgical Build" (Pro Mode)
If you want to hit the absolute minimum size, you can surgically exclude "ghost" dependencies like `pygame` that might be sitting in your environment:
```powershell
uv run --extra build build.py --spec-filter --exclude-qt --exclude-module pygame
```

---

## 🧪 Method 2: Nuitka (The Pro Compiler)
Nuitka translates your Python code into C++ and compiles it into a native binary. This results in **25% less RAM usage** and faster execution.

### Setup (One-time):
1.  **Install build tools**: `uv sync --extra build` or `pip install .[build]`
> [!NOTE]
> Nuitka will ask to download a C++ compiler on the first run. Just say 'Yes'.

### Build Commands:
- **For a single executable**: `uv run nuitka_build.py --onefile`
- **For a folder**: `uv run nuitka_build.py --onedir`

---

## 📊 Benchmarks & Analysis
For detailed data and analysis, check out my full **[Size & Performance Report](BENCHMARKS.md)**

---

**📖 Full distribution tips: [DISTRIBUTION_FAQ.md](DISTRIBUTION_FAQ.md)**