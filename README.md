# Circuit Playground Pro - Qt Version

Modern, professional circuit simulator built with PySide6 (Qt for Python).

## 🚀 Features

- **Modern UI/UX**: Dark theme with professional styling using QSS
- **QGraphicsScene Canvas**: Smooth rendering with anti-aliasing
- **Pan & Zoom**: Middle-mouse to pan, scroll wheel to zoom
- **Dock Widgets**: Movable, floatable component library and property panels
- **Full Functionality**:
  - Save/Load circuits
  - Undo/Redo (50 levels)
  - Component rotation (0°, 90°, 180°, 270°)
  - Wire routing with waypoints
  - Dynamic component properties
  - Real-time simulation
  - **truth-table generation**

## 📦 Installation

```powershell
# use requirements file
pip install -r requirements.txt
```

## ▶️ Run

```powershell
python app.py
```

## 📦 Distribution

### Standalone Executable

Build a Windows executable that requires no Python installation:

```powershell
python build.py
```

**📖 Documentation:**

- **[BUILD_INSTRUCTIONS.md](docs/BUILD_INSTRUCTIONS.md)** - How to build the executable
- **[EXE_DISTRIBUTION_FAQ.md](docs/EXE_DISTRIBUTION_FAQ.md)** - Everything about the .exe, distribution, and platform support

## 🎮 Controls

### Mouse

- **Left-click drag (canvas)**: Pan view
- **Middle mouse / Ctrl+click**: Pan view
- **Scroll wheel**: Zoom in/out
- **Click component**: Select it
- **Drag component**: Move it
- **Double-click INPUT**: Toggle ON/OFF
- **Click output pin**: Start wire
- **Click input pin**: Complete wire
- **Click while wiring**: Add waypoint
- **Right-click input pin**: Remove wire

### Keyboard Shortcuts

- **Ctrl+N**: New circuit
- **Ctrl+S**: Save circuit
- **Ctrl+L**: Load circuit
- **Ctrl+Z**: Undo
- **Ctrl+Y**: Redo
- **Delete**: Delete selected
- **Q**: Rotate components counter-clockwise
- **E**: Rotate components clockwise
- **R**: Reset view
- **G**: Toggle grid
- **C**: Toggle component library
- **P**: Toggle properties panel
- **Escape**: Cancel wire connection

## 🏗️ Architecture

### Core

- `core/base.py` - Gate, Pin, Wire classes
- `core/logic_gates.py` - AND, OR, NOT, XOR, NAND, NOR, XNOR
- `core/advanced.py` - MUX, DEMUX, Encoder, Decoder
- `core/io.py` - InputSwitch, OutputLED

### Qt UI Layer

- `ui/theme.py` - Modern dark theme with QSS styling
- `ui/items.py` - GateItem, PinItem, WireItem graphics
- `ui/canvas.py` - QGraphicsView with pan/zoom and wire connections
- `ui/components.py` - Dock widgets, dialogs, property panels

### Main Application

- `simulator/` **package** — codebase refactored into a small, modular package (`main.py`, `persistence.py`, `truthtable.py`, `utils.py`, `setup.py`) to improve testability and maintainability; `app.py` (at the project root) remains the entry script that starts the app.

- Persistence & format — circuits are saved in **YAML** and the persistence layer now stores stable `uid` values for gates and annotations to preserve selection and history across save/load.

## 🎨 UI Components

### QGraphicsItems

- **GateItem**: Custom graphics item for logic gates with rotation
- **PinItem**: Connection points with hover effects
- **WireItem**: QPainterPath-based wires with waypoints
- **TextAnnotationItem**: Editable text annotation with font and color options
- **RectangleAnnotationItem**: Rectangle annotation with border radius and color
- **CircleAnnotationItem**: Circular annotation for highlighting regions

### Widgets & Views

- **CircuitCanvas**: `QGraphicsView` that hosts the scene; handles pan/zoom, selection, and wire interactions
- **ComponentLibrary**: `QDockWidget` with `QListWidget` for adding components
- **PropertyPanel**: Dynamic property editor with controls and live value updates
- **InputDialog**: Modern text input dialog
- **FileListDialog**: Circuit file selector
- **ConfirmDialog**: Custom confirmation dialog
- **SettingsDialog**: Preferences dialog for canvas/grid/FPS
- **GlobalSettingsDialog**: App-level settings (undo/redo history limit, etc.)
- **HelpDialog**: Rich HTML help dialog shown from the Help menu

## 🎯 Key Improvements over Pygame

1. **Native Look & Feel**: Uses OS-native widgets and rendering
2. **Better Text Rendering**: Anti-aliased fonts, no pixelation
3. **Better Scaling**: DPI-aware rendering

## 🔧 Customization

### Theme

Edit `ui/theme.py` to customize colors and QSS styles.

### Canvas

Adjust grid size, zoom limits in `ui/canvas.py`.

## Case Study: Large Truth-Table Memory (>2^16 rows) 💾

**Problem:** Generating very large truth tables (e.g., 16 inputs → 65,536 rows) produced a large process Resident Set Size (RSS is the amount of physical RAM a process currently occupies) spike while the table was displayed (observed peaks ≈ 800+ MB for 65K+ rows) and was leaving elevated memory after the dialog was closed in earlier builds.

**Mitigations / fixes applied:**

- Root cause: the original item-based viewer created a `QTableWidgetItem` for every cell which triggered large C++/Qt allocations and produced massive RSS spikes for large truth tables (e.g., 2^16 rows). Releasing Python references alone wasn't sufficient to immediately reclaim that C++ memory due to allocator behavior and Qt caches.

- `simulator/main.py`:

  - Pauses simulation and suspends UI updates while a model-based truth-table view runs; ensures simulator state is restored and UI updates resume after the dialog is closed.

- `ui/components/truthtabledialog.py`:

  - Replaced the item-based truth-table viewer with a lazy model-based view (`QAbstractTableModel` + `QTableView`) to eliminate per-cell `QTableWidgetItem` allocations that caused RSS spikes.
  - Redesigned export to run in small, cancelable chunks on the main thread (saves to Downloads when possible), and added a centralized `_cleanup()` method that closes export files, removes temporary CSV files, detaches the model (`setModel(None)`), schedules safe Qt widget deletion (`deleteLater()`), processes pending Qt events, and calls `gc.collect()` on close — together these prevent leaks, races, and UI hangs.
  - Hooked `_cleanup()` into `accept()`, `reject()` and `closeEvent()` so cleanup runs reliably regardless of how the dialog is closed.

- Additional improvements:
  - Removed in-memory preview/fallbacks, improved Cancel/Close behavior during export, and replaced fragile thread usage with a safe chunked main‑thread exporter (avoids unsafe cross‑thread access to Qt objects and prevents hangs/races).
  - Added logging for export errors, deterministic file cleanup, and immediate Export-button disable to avoid leaving temp files locked on Windows and prevent double-started exports; exported CSVs are saved to the user's Downloads folder when available (fallback to a temp file otherwise).

**Observed results:**

- Previously, peak memory while the table was shown could reach ~800 MB (example run) due to per-cell Qt allocations.
- In the current implementation the large RSS spike is no longer reproducible in smoke tests; opening very large truth tables now keeps memory near baseline (typically ≈ 40-45 MB) during and after the dialog is closed.

## 📝 Notes

- Simulation runs at ~60 FPS (QTimer with 16ms interval)
- Supports up to 50 undo/redo levels
- Circuits saved in `save_files/circuits/` directory
