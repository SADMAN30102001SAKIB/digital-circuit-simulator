from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QToolBar


def setup_toolbar(sim):
    toolbar = QToolBar("Main Toolbar")
    toolbar.setMovable(False)
    sim.addToolBar(toolbar)

    action_new = QAction("New", sim)
    action_new.setShortcut(QKeySequence.New)
    action_new.setToolTip("New circuit (Ctrl+N)")
    action_new.triggered.connect(sim.new_circuit)
    toolbar.addAction(action_new)

    action_save = QAction("Save", sim)
    action_save.setShortcut(QKeySequence.Save)
    action_save.setToolTip("Save circuit (Ctrl+S)")
    action_save.triggered.connect(
        lambda: __import__("simulator").persistence.save_circuit(sim)
    )
    toolbar.addAction(action_save)

    action_load = QAction("Load", sim)
    action_load.setShortcut("Ctrl+L")
    action_load.setToolTip("Load circuit (Ctrl+L)")
    action_load.triggered.connect(
        lambda: __import__("simulator").persistence.load_circuit(sim)
    )
    toolbar.addAction(action_load)

    toolbar.addSeparator()

    action_undo = QAction("Undo", sim)
    action_undo.setShortcut(QKeySequence.Undo)
    action_undo.setToolTip("Undo (Ctrl+Z)")
    action_undo.triggered.connect(sim.undo)
    toolbar.addAction(action_undo)

    action_redo = QAction("Redo", sim)
    action_redo.setShortcut(QKeySequence.Redo)
    action_redo.setToolTip("Redo (Ctrl+Y)")
    action_redo.triggered.connect(sim.redo)
    toolbar.addAction(action_redo)

    toolbar.addSeparator()

    action_reset = QAction("Reset View", sim)
    action_reset.setToolTip("Reset view (R)")
    action_reset.triggered.connect(sim.canvas.reset_view)
    toolbar.addAction(action_reset)

    action_delete = QAction("Delete", sim)
    action_delete.setShortcut(QKeySequence.Delete)
    action_delete.setToolTip("Delete selected (Del)")
    action_delete.triggered.connect(sim.delete_selected)
    toolbar.addAction(action_delete)


def setup_statusbar(sim):
    from PySide6.QtWidgets import QStatusBar

    sim.statusbar = QStatusBar()
    sim.setStatusBar(sim.statusbar)
    sim.statusbar.showMessage(
        "Pan: Drag | Wire: Click output→input | Rotate: Q/E | Toggle input: Double-click"
    )


def setup_menu(sim):
    menubar = sim.menuBar()

    file_menu = menubar.addMenu("&File")
    file_menu.addAction("&New (Ctrl+N)", sim.new_circuit)
    file_menu.addAction(
        "&Save (Ctrl+S)", lambda: __import__("simulator").persistence.save_circuit(sim)
    )
    file_menu.addAction(
        "&Load (Ctrl+L)", lambda: __import__("simulator").persistence.load_circuit(sim)
    )
    file_menu.addSeparator()
    file_menu.addAction("E&xit", sim.close)

    edit_menu = menubar.addMenu("&Edit")
    edit_menu.addAction("&Undo (Ctrl+Z)", sim.undo)
    edit_menu.addAction("&Redo (Ctrl+Y)", sim.redo)
    edit_menu.addSeparator()
    edit_menu.addAction("&Delete (Del)", sim.delete_selected)

    view_menu = menubar.addMenu("&View")

    action_reset = view_menu.addAction("&Reset View", sim.canvas.reset_view)
    action_reset.setShortcut("R")

    action_grid = view_menu.addAction("Toggle &Grid", sim._toggle_grid)
    action_grid.setShortcut("G")

    view_menu.addSeparator()

    action_components = view_menu.addAction(
        "&Component Library", sim._toggle_component_library
    )
    action_components.setShortcut("C")

    action_props = view_menu.addAction("&Properties", sim._toggle_properties)
    action_props.setShortcut("P")

    settings_menu = menubar.addMenu("&Settings")
    settings_menu.addAction("&Preferences...", sim._show_settings)
    settings_menu.addAction("&Global Settings...", sim._show_global_settings)

    help_menu = menubar.addMenu("&Help")
    help_menu.addAction("&How to Use", sim._show_help)
    help_menu.addAction("&About", sim._show_about)
