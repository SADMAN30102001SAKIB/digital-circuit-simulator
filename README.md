# Circuit Playground Pro (v3.1.3)

Modern, professional logic circuit simulator built with **PySide6** (Qt for Python). Optimized for high-performance simulation and automated logic analysis.

## 🚀 Key Features

- **100% Verified Logic**: Comprehensive test suite ensuring 57+ edge cases are error-free.
- **Modern UI/UX**: Sleek dark theme with professional QSS styling.
- **High-Performance Canvas**: Smooth rendering with anti-aliasing and smart zoom/pan.
- **Smart Component Naming**: Automated label generation for inputs (`IN1`, `IN2`, etc.) used across the canvas and truth tables.
- **Advanced Truth Table Generator**:
  - **Millions of Rows**: Optimized virtual view handles 20+ inputs instantly.
  - **Zero Frame Drop**: Background analysis and chunked exports.
  - **CSV Export**: Direct-to-Downloads export for external verification.
- **Full-Featured Suite**:
  - **YAML Persistence**: Scalable, human-readable circuit saves.
  - **Branching Undo/Redo**: Up to 200 history levels with smart state tracking.
  - **Advanced Gates**: MUX, DEMUX, Encoders, Decoders, and custom Annotations.
  - **Movable UI**: Floatable dock widgets for component library and property panels.


## 📋 Prerequisites (Linux)
To run or build the Linux version, you **must** install the X11/Qt dependencies. These are required for the application to render graphics and handle window events.

**Graphical Dependencies:**
```bash
sudo apt update && sudo apt install -y --no-install-recommends libgl1 libegl1 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-image0 libxcb-shm0 libxcb-render-util0 libxcb-xkb1 libxkbcommon-x11-0 libxcb-shape0 libxcb-util1 libxcb-xinerama0 libxcb-xinput0 libopengl0
```

## 📦 Installation & Usage
> [!NOTE]
> This project is optimized and tested for **Python 3.10 through 3.12**.

### 🚀 Fast Track (Using `uv`)
Recommended for speed and simplicity.
```bash
# Install uv (one-time)
# Windows: 
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/macOS: 
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run application (auto-installs dependencies)
uv run app.py
```

### 🐍 Standard Python
```bash
# Create and activate virtual environment
python -m venv .venv
# Windows: 
.venv\Scripts\activate
# Linux/macOS: 
source .venv/bin/activate

# Install dependencies from pyproject.toml
pip install .

# Launch application
python app.py
```

### 🧪 Running Tests
The project uses `pytest` and `pytest-qt` for high-integrity verification.
```bash
# Install dependencies
uv sync --extra test
# Run all tests
uv run python -m pytest tests

# if you're on a headless server, you can run tests like this:
# Linux/macOS (headless)
QT_QPA_PLATFORM=offscreen uv run python -m pytest tests
# Windows PowerShell (headless)
$env:QT_QPA_PLATFORM="offscreen"; uv run python -m pytest tests
```

### 🧹 Quality Control (Linter)
I use **Ruff** for sub-second linting and formatting. 
```bash
# Check for errors and auto-fixable issues
uv run ruff check . --fix
# Standardize formatting
uv run ruff format .
```

## 📚 Sample Circuits

The `examples/` folder contains pre-built circuits you can load into the app:

### How to Use:
Run the app at least once to create the save files directory. Then copy any `.yaml` file from `examples/` into the app's circuit folder:

| OS | Circuit Folder Location |
|----|------------------------|
| **Windows** | `Documents\CircuitPlaygroundPro\circuits\` |
| **macOS** | `~/Documents/CircuitPlaygroundPro/circuits/` |
| **Linux** | `~/Documents/CircuitPlaygroundPro/circuits/` |
| **Fallback** | `./save_files/circuits/` (`./` means app's root directory) |

Then open the app and use **Ctrl+L** (or **Cmd+L** on Mac) to load it.
    
> [!TIP]
> **Note**: If Windows Defender blocks the app from accessing your **Documents** folder (Controlled Folder Access), you can verify and unblock it easily:
> 1. Search for **Windows Security** in the Start menu.
> 2. Go to **Virus & threat protection** > **Protection history**.
> 3. Under the **Protected folder access blocked** entry, find the app name.
> 4. Click the **Actions** button and select **Allow on device**.

## 🎮 Controls & Shortcuts

- **Mouse**: Pan with Left-drag/Middle-click, Scroll to Zoom, Double-click INPUTs to toggle.
- **Wires**: Click Output pin (right) then click Input pin (left). Click empty space while wiring to add waypoints.
- **Ctrl/Cmd + S / L**: Save / Load Circuit
- **Ctrl/Cmd + Z / Y**: Undo / Redo
- **Q / E**: Rotate components
- **Delete**: Remove selected item
- **Escape**: Cancel wiring or selection

## 🏗️ Building Executable

The project includes a robust build system to create the smallest possible standalone executables (~21MB) using PyInstaller or Nuitka.

**📖 Documentation:**
- **[BUILD_INSTRUCTIONS.md](docs/BUILD_INSTRUCTIONS.md)** - detailed build flags.

## 🏗️ Architecture

The codebase is organized into a clean, modular package structure:
- **`core/`**: Mathematical logic and component definitions.
- **`ui/`**: Qt-based rendering, custom GraphicsItems, and windowing.
- **`simulator/`**: Application controller, persistence layer, and truth-table logic.
- **`assets/`**: Icons, styles, and help documentation.

## 🎯 Technical Case Study: Memory Optimization (v3.x.x)

**The Challenge: The "Greedy" UI Problem**  
In previous versions, generating a Truth Table for a 16-input circuit (65,536 rows) would cause a massive RAM spike (800MB+). This happened because the app used an **item-based table** (`QTableWidget`), which creates a unique UI object for every single cell. For a large table, this meant generating over **1.1 million objects** in memory simultaneously, overwhelming both the Python heap and the C++/Qt allocator.

**The Solution: The "Lazy" Model Transformation**  
The **v3.x.x Advanced Audit Edition** completely re-engineered the analysis engine using a **Model-View Architecture**:

1.  **Lazy Loading (`QAbstractTableModel`)**: Instead of pre-creating millions of widgets, the app now uses a virtual model. It only "renders" the data for the specific cells currently visible on your screen. This dropped the active memory footprint from 800MB down to a stable **~75MB**.
2.  **Deterministic Cleanup**: Python's garbage collector doesn't always reclaim C++ resources immediately. I implemented a centralized `_cleanup()` routine that explicitly detaches models, clears temporary export files, and triggers `gc.collect()` upon closing the dialog.

**Result**: Professional-grade performance where analysis remains snappy even as circuit complexity grows exponentially.

## 🔮 Future Roadmap
- [x] **Persistent Window State**: Stop resizing the window every time you open it.
- [x] **Unified Resource Paths**: Centralized path resolution ensuring icons and data load perfectly whether running as a raw script, a PyInstaller bundle, or a Nuitka Native binary.
- [x] **Professional Logging**: No more print() to hidden terminals - proper log file named `simulator.log` in the `save_files` directory of the application for debugging.
- [ ] **Sequential Logic (Memory)**: Implement storage elements like **Flip-flops (D, JK, SR, T)**, Counters, and Shift Registers. Add a **Clock Input** component with configurable frequency to drive temporal logic.
- [ ] **Waveform Analyzer**: A real-time logic analyzer to record and visualize signal transitions over time. Essential for debugging sequential logic, catching glitches, and measuring propagation delays.
- [ ] **Sub-circuits (The "Chip" Builder)**: Enable modularity by allowing users to encapsulate circuits (like a 4-bit Adder) into reusable custom blocks.

## 📝 Project Details
- **Version**: 3.1.3 (Professional Edition)
- **Engine**: PySide6 (Qt)
- **Quality**: Verified by 57+ test cases & Ruff Linting (PEP 8)
- **Continuous Delivery**: **[Windows vs. The World](docs/CD_CASE_STUDY.md)** - A technical case study on why development on Linux feels like magic while Windows feels like a haunted toaster.
- **Continuous Integration**: Automated tests on Windows, Linux, and macOS via GitHub Actions.
- **Health**: 100% (Includes `MIT License`, `Security Policy`, `Code of Conduct`, and `Contribution Guidelines`)

- **Persistence**: YAML structure with stable UIDs.
