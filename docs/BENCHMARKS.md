# 📉 Benchmark Report & Analysis

This document provides a deep dive into the size and performance of Circuit Playground Pro across different build configurations.

## 📊 The "Extreme Engineering" Benchmarks (v3.1.3)

This is the complete, line-for-line breakdown of every build combination tested during the v3.1.3 optimization sprint.

> [!NOTE]
> All detailed benchmarks below were performed on a local **Windows 11** machine. Unix builds are naturally larger (see Section 4).

### 🧪 PyInstaller: Onefile (Single Executable)
The goal for onefile is portability. These benchmarks show the impact of **Spec-Filtering** and **UPX**.

| Configuration | With UPX (Standard) | No UPX (`--no-upx`) | Compression Impact |
| :--- | :--- | :--- | :--- |
| **Default Build** | ~40 MB | ~45 MB | ~-5 MB |
| **+ Exclude-Qt** | ~40 MB | ~44 MB | ~-4 MB |
| **+ Spec-Filter** | ~25 MB | ~27 MB | ~-2 MB |
| **+ Spec-Filter + Exclude-Qt** | ~22 MB | ~24 MB | ~-2 MB |
| **+ Spec-Filter + Exclude-Qt + Exclude-Module-pygame** | **~21 MB** | ~23 MB | ~-2 MB |

### 🧪 PyInstaller: Onedir (Distribution Folder)
Folder builds are best for speed and professional installers. Here, the **Pruning** script is the MVP.

| Configuration | With UPX (Standard) | No UPX (`--no-upx`) | Compression Impact |
| :--- | :--- | :--- | :--- |
| **Default Build** | ~79 MB | ~111 MB | ~-32 MB |
| **+ Exclude-Qt** | ~78 MB | ~109 MB | ~-31 MB |
| **+ Pruning** | ~52 MB | ~85 MB | ~-33 MB |
| **+ Pruning + Exclude-Qt** | ~52 MB | ~84 MB | ~-32 MB |
| **+ Spec-Filter** | ~50 MB | ~67 MB | ~-18 MB |
| **+ Spec-Filter + Exclude-Qt** | ~46 MB | ~61 MB | ~-14 MB |
| **+ Spec-Filter + Pruning** | ~44 MB | ~61 MB | ~-17 MB |
| **+ Spec-Filter + EX-Qt + Prune** | **~37 MB** | **~55 MB** | **~-18 MB** |

### 🧪 Nuitka: The Compiler Alternative
Nuitka doesn't have "layers"—it uses deep static analysis to include only what is needed automatically.

| Nuitka Configuration | Resulting Size | Performance Note |
| :--- | :--- | :--- |
| **Onefile Executable** | **~22 MB** | Matches our best PyInstaller build |
| **Onedir Folder** | ~76 MB | Larger than PyInstaller but very stable |

---

## 🔬 Deep Dive: The "Why" Behind the Numbers

### 1. Scaling the "Wall" (Why ~21MB is the limit)
You might notice that both our most optimized PyInstaller build and our Nuitka build hit a "floor" at **~21 MB**. This is because:
*   **The Runtime Engine**: Python needs its base logic (~9MB).
*   **The UI Engine**: Qt (PySide6) needs its core graphical logic (~12MB).
*   **The Result**: ~21MB is the absolute minimum "Skeleton" required for a modern Python GUI to exist.

### 2. PyInstaller's Three Optimization Layers
*   **`--exclude-qt`**: Strips the Python "code libraries" for parts we don't use (like QML, WebEngine, and Network).
*   **`--prune`**: Acts like a "Janitor" for folder builds. It goes into the folder after building and throws away 40MB of unused translation files (e.g., German, Chinese) and DLL fragments.
*   **`--spec-filter`**: This is our most powerful weapon. Instead of letting PyInstaller "guess" what we need, we give it a strict **Whitelist**. If it's not on the list (like PDF drivers or Bluetooth), it's not in the executable.

### 3. The UPX Effect (Folder Savior)
Without UPX compression, a standard folder build is **~111 MB**. With UPX, it drops to **~79 MB**.
*   **Why?** UPX "squashes" raw DLL files using clever math. It’s essential for folder builds because those files sit there uncompressed. In a single executable, its effect is smaller because the executable already has its own internal "zip" compression.

### 4. Windows vs. Linux: The Size Gap
You might notice Linux builds are consistently larger. This is normal and unavoidable for three reasons:
*   **Batteries Included**: Windows has built-in system DLLs (`kernel32`, `user32`) that I assume exist. Linux has many distributions, so we must bundle basic system libraries (`libstdc++`, `liblzma`) to ensure the app runs on any distro.
*   **The GUI Stack**: On Windows, the window manager is part of the kernel. On Linux, we must bundle a heavy chain of X11 libraries (`libxcb`, `libX11`, etc.) just to draw a window.
*   **Portable Runtime**: Nuitka/PyInstaller bundle a private copy of the C runtime for Linux compatibility, adding ~10MB overhead that Windows builds don't need.

### 5. Nuitka: The Performance King 👑
On Windows, Nuitka builds take almost similar `Disk Space` as PyInstaller (but on unix, Nuitka builds are surprisingly smaller). 
But **Memory (RAM) Usage** is where the two methods diverge significantly.

| Application State | PyInstaller Build | Nuitka Build | Efficiency Gain |
| :--- | :--- | :--- | :--- |
| **Idle / Startup** | ~68–71 MB | **~50–52 MB** | **~26% Less** |
| **Generating Truth Table** | ~76–77 MB | **~57–60 MB** | **~25% Less** |

**The "Why"**: PyInstaller is a "Bundler" (it carries the code); Nuitka is a "Compiler" (it turns the code into machine language). Compiled code uses less RAM because it doesn't need to load the Python interpreter's "instruction manual" into memory while it runs.

---

## 🏆 Final Verdict

*   **For Development**: Use `build.py`. It's fast (30 sec) and very flexible.
*   **For Distribution**: Use **Nuitka** for the best RAM performance.

**📖 Full distribution tips: [DISTRIBUTION_FAQ.md](DISTRIBUTION_FAQ.md)**