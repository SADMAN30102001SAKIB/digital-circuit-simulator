# Circuit Playground Pro (v3.1.0)

Modern, professional logic circuit simulator built with **PySide6** (Qt for Python). Optimized for high-performance simulation and automated logic analysis.

## 🚀 Key Features

- **100% Verified Logic**: Comprehensive test suite ensuring 27+ edge cases are error-free.
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

## 📦 Installation & Usage

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
# Run all tests (headless)
uv run python -m pytest tests/
```

### 🧹 Quality Control (Linter)
We use **Ruff** for sub-second linting and formatting. 
```bash
# Check for errors and auto-fixable issues
uv run ruff check . --fix
# Standardize formatting
uv run ruff format .
```

## 🏗️ Building Executable

The project includes a robust build system to create small, standalone executables (~21MB) using PyInstaller or Nuitka.

**📖 Documentation:**
- **[BUILD_INSTRUCTIONS.md](docs/BUILD_INSTRUCTIONS.md)** - detailed build flags.

## 🎮 Controls & Shortcuts

- **Mouse**: Pan with Left-drag/Middle-click, Scroll to Zoom, Double-click INPUTs to toggle.
- **Wires**: Click Output pin (right) then click Input pin (left). Click empty space while wiring to add waypoints.
- **Ctrl/Cmd + S / L**: Save / Load Circuit
- **Ctrl/Cmd + Z / Y**: Undo / Redo
- **Q / E**: Rotate components
- **Delete**: Remove selected item
- **Escape**: Cancel wiring or selection

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
2.  **Deterministic Cleanup**: Python's garbage collector doesn't always reclaim C++ resources immediately. We implemented a centralized `_cleanup()` routine that explicitly detaches models, clears temporary export files, and triggers `gc.collect()` upon closing the dialog.

**Result**: Professional-grade performance where analysis remains snappy even as circuit complexity grows exponentially.

## 🔮 Future Roadmap

- [ ] **Sequential Logic (Memory)**: Implement storage elements like **Flip-flops (D, JK, SR, T)**, Counters, and Shift Registers. Add a **Clock Input** component with configurable frequency to drive temporal logic.
- [ ] **Waveform Analyzer**: A real-time logic analyzer to record and visualize signal transitions over time. Essential for debugging sequential logic, catching glitches, and measuring propagation delays.
- [ ] **Sub-circuits (The "Chip" Builder)**: Enable modularity by allowing users to encapsulate circuits (like a 4-bit Adder) into reusable custom blocks.

## 📝 Project Details
- **Version**: 3.1.0 (Professional Edition)
- **Engine**: PySide6 (Qt)
- **Quality**: Verified by 27+ tests & Ruff Linting (PEP 8)
- **Continuous Integration**: Automated tests on Windows, Linux, and macOS via GitHub Actions.
- **Health**: 100% (Includes `MIT License`, `Code of Conduct`, and `Contribution Guidelines`)
- **Persistence**: YAML structure with stable UIDs.