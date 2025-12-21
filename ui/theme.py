# Color palette - Modern dark theme
CANVAS_BG = "#28292E"
NAVBAR_BG = "#14161A"
TEXT_COLOR = "#DCDCE1"
TEXT_DIM = "#969699"
ACCENT = "#5096FF"
SUCCESS = "#50C878"
DANGER = "#FF5050"
WIRE_ACTIVE = "#50C878"
WIRE_INACTIVE = "#505560"
SELECTION = "#FFC832"
GRID_COLOR = "#323438"

# Component colors
GATE_COLORS = {
    "AND": "#4678C8",
    "OR": "#C8644E",
    "NOT": "#964EC8",
    "XOR": "#C89646",
    "NAND": "#6496C8",
    "NOR": "#DC7858",
    "XNOR": "#B4AA5A",
    "MUX": "#78B48C",
    "DEMUX": "#8C78B4",
    "ENCODER": "#B48C78",
    "DECODER": "#788CB4",
    "INPUT": SUCCESS,
    "LED": DANGER,
    # Annotations
    "TEXT": "#DCDCE1",
    "RECT": "#5096FF",
    "CIRCLE": "#5096FF",
}

# Modern QSS stylesheet
MODERN_STYLE = """
/* Main Window */
QMainWindow {
    background-color: #1E1E23;
}

/* Toolbar */
QToolBar {
    background-color: #14161A;
    border: none;
    border-bottom: 2px solid #3C3E44;
    spacing: 8px;
    padding: 8px;
}

QToolBar::separator {
    background-color: #3C3E44;
    width: 2px;
    margin: 4px 8px;
}

/* Buttons */
QPushButton {
    background-color: #5096FF;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #64AAFF;
}

QPushButton:pressed {
    background-color: #3C82E6;
}

QPushButton:disabled {
    background-color: #3C3E44;
    color: #5E6066;
}

QPushButton[class="success"] {
    background-color: #50C878;
}

QPushButton[class="success"]:hover {
    background-color: #64DC8C;
}

QPushButton[class="danger"] {
    background-color: #FF5050;
}

QPushButton[class="danger"]:hover {
    background-color: #FF6464;
}

/* Small / compact buttons */
QPushButton[class~="small"] {
    padding: 4px 8px;
    font-size: 12px;
    min-height: 24px;
    border-radius: 4px;
}

QPushButton[class~="small"][class~="danger"] {
    background-color: #FF5050;
}

/* Tool Buttons (in toolbar) */
QToolButton {
    background-color: transparent;
    color: #DCDCE1;
    border: none;
    border-radius: 4px;
    padding: 8px;
    font-weight: bold;
}

QToolButton:hover {
    background-color: #2A2C31;
}

QToolButton:pressed {
    background-color: #3C3E44;
}

/* Dock Widgets */
QDockWidget {
    background-color: #191B1F;
    color: #DCDCE1;
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
    border: none;
}

QDockWidget::title {
    background-color: #14161A;
    padding: 12px 16px;
    border-bottom: 2px solid #3C3E44;
    font-weight: bold;
    font-size: 14px;
}

QDockWidget::close-button, QDockWidget::float-button {
    padding: 0px;
    border: none;
    background: transparent;
}

/* Scroll Area */
QScrollArea {
    background-color: #191B1F;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: #191B1F;
}

/* List Widgets */
QListWidget {
    background-color: #191B1F;
    color: #DCDCE1;
    border: none;
    outline: none;
    padding: 4px;
    font-size: 13px;
}

QListWidget::item {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 10px 12px;
    margin: 2px 4px;
}

QListWidget::item:hover {
    background-color: #2A2C31;
}

QListWidget::item:selected {
    background-color: #5096FF;
    color: #FFFFFF;
}

/* Scroll Bars */
QScrollBar:vertical {
    background-color: #191B1F;
    width: 12px;
    margin: 0px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #3C3E44;
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4E5056;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #191B1F;
    height: 12px;
    margin: 0px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #3C3E44;
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4E5056;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

QLineEdit {
    background-color: #28292E;
    color: #DCDCE1;
    border: 2px solid #3C3E44;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #5096FF;
}

QPlainTextEdit {
    background-color: #28292E;
    color: #DCDCE1;
    border: 2px solid #3C3E44;
    border-radius: 6px;
    padding: 8px 12px; /* Standardized to match QLineEdit */
    font-size: 13px;
    selection-background-color: #5096FF;
}

QLineEdit:focus, QPlainTextEdit:focus {
    border-color: #5096FF;
}

QLineEdit:disabled, QPlainTextEdit:disabled {
    background-color: #1E1E23;
    color: #5E6066;
}

/* Labels */
QLabel, QCheckBox {
    color: #DCDCE1;
    font-size: 13px;
    background-color: transparent;
}

QLabel[class="title"] {
    font-size: 16px;
    font-weight: bold;
    padding: 4px 0px;
}

QLabel[class="dim"] {
    color: #969699;
}

/* Spinbox */
QSpinBox, QDoubleSpinBox {
    background-color: #28292E;
    color: #DCDCE1;
    border: 2px solid #3C3E44;
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 13px;
}

QSpinBox:focus, QDoubleSpinBox:focus, QFontComboBox:focus {
    border-color: #5096FF;
}

/* Font Combo Box Fix */
QFontComboBox {
    background-color: #28292E;
    color: #DCDCE1;
    border: 2px solid #3C3E44;
    border-radius: 6px;
    padding: 4px 8px;
}

/* Hide up/down buttons and arrows for a cleaner look */
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    width: 0px;
    border: none;
    background: transparent;
}

QSpinBox::up-arrow, QSpinBox::down-arrow,
QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    border: none;
    width: 0px;
    height: 0px;
}

/* Group Box */
QGroupBox {
    background-color: transparent;
    border: 2px solid #3C3E44;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px; /* Reduced from 16px */
    font-weight: bold;
}

QGroupBox::title {
    color: #DCDCE1;
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    background-color: #1E1E23;
    border-radius: 4px;
    left: 12px;
}

/* Dialog */
QDialog {
    background-color: #1E1E23;
}

/* Status Bar */
QStatusBar {
    background-color: #14161A;
    color: #969699;
    border-top: 2px solid #3C3E44;
    font-size: 12px;
}

/* Menu Bar */
QMenuBar {
    background-color: #14161A;
    color: #DCDCE1;
    border-bottom: 2px solid #3C3E44;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 8px 12px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #2A2C31;
}

QMenuBar::item:pressed {
    background-color: #3C3E44;
}

/* Menu */
QMenu {
    background-color: #191B1F;
    color: #DCDCE1;
    border: 2px solid #3C3E44;
    border-radius: 8px;
    padding: 8px;
}

QMenu::item {
    background-color: transparent;
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #5096FF;
}

QMenu::separator {
    height: 2px;
    background-color: #3C3E44;
    margin: 6px 8px;
}

/* Graphics View (Canvas) */
QGraphicsView {
    background-color: #28292E;
    border: none;
}

/* Tab Widget */
QTabWidget::pane {
    background-color: #191B1F;
    border: 2px solid #3C3E44;
    border-radius: 8px;
    top: -2px;
}

QTabBar::tab {
    background-color: #28292E;
    color: #969699;
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background-color: #5096FF;
    color: #FFFFFF;
}

QTabBar::tab:hover:!selected {
    background-color: #3C3E44;
}

/* Tooltips */
QToolTip {
    background-color: #14161A;
    color: #DCDCE1;
    border: 2px solid #5096FF;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}
"""
