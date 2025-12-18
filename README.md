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
  - **truth-table generator** with a progress dialog and cancel support

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

## 📝 Notes

- Simulation runs at ~60 FPS (QTimer with 16ms interval)
- Supports up to 50 undo/redo levels
- Circuits saved in `save_files/circuits/` directory
