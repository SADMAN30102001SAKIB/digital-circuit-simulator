from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QToolBar

import simulator.persistence as persistence


def setup_toolbar(sim):
    toolbar = QToolBar("Main Toolbar")
    toolbar.setMovable(False)
    sim.addToolBar(toolbar)

    sim.action_new = QAction("New", sim)
    sim.action_new.setShortcut(QKeySequence.New)
    sim.action_new.setToolTip("New circuit (Ctrl+N)")
    sim.action_new.triggered.connect(sim.new_circuit)
    toolbar.addAction(sim.action_new)

    sim.action_save = QAction("Save", sim)
    sim.action_save.setShortcut(QKeySequence.Save)
    sim.action_save.setToolTip("Save circuit (Ctrl+S)")
    sim.action_save.triggered.connect(lambda: persistence.save_circuit(sim))
    toolbar.addAction(sim.action_save)

    sim.action_load = QAction("Load", sim)
    sim.action_load.setShortcut("Ctrl+L")
    sim.action_load.setToolTip("Load circuit (Ctrl+L)")
    sim.action_load.triggered.connect(lambda: persistence.load_circuit(sim))
    toolbar.addAction(sim.action_load)

    toolbar.addSeparator()

    sim.action_undo = QAction("Undo", sim)
    sim.action_undo.setShortcut(QKeySequence.Undo)
    sim.action_undo.setToolTip("Undo (Ctrl+Z)")
    sim.action_undo.triggered.connect(sim.undo)
    toolbar.addAction(sim.action_undo)

    sim.action_redo = QAction("Redo", sim)
    import platform
    current_os = platform.system()
    if current_os == "Linux":
        # On Linux, QKeySequence.Redo is usually Ctrl+Shift+Z. 
        # We explicitly add Ctrl+Y for parity with the Windows experience.
        sim.action_redo.setShortcuts([QKeySequence.Redo, "Ctrl+Y"])
    elif current_os == "Darwin":
        # On Mac, Redo is always Command+Shift+Z
        sim.action_redo.setShortcut("Ctrl+Shift+Z") # Qt translates Ctrl to Cmd on Mac
    else:
        # On Windows, QKeySequence.Redo already includes Ctrl+Y.
        sim.action_redo.setShortcut(QKeySequence.Redo)
        
    sim.action_redo.setToolTip("Redo (Ctrl+Shift+Z)")
    sim.action_redo.triggered.connect(sim.redo)
    toolbar.addAction(sim.action_redo)

    toolbar.addSeparator()

    sim.action_reset = QAction("Reset View", sim)
    sim.action_reset.setShortcut("R")
    sim.action_reset.setToolTip("Reset view (R)")
    sim.action_reset.triggered.connect(sim.canvas.reset_view)
    toolbar.addAction(sim.action_reset)

    sim.action_delete = QAction("Delete", sim)
    sim.action_delete.setShortcut(QKeySequence.Delete)
    sim.action_delete.setToolTip("Delete selected (Del)")
    sim.action_delete.triggered.connect(sim.delete_selected)
    toolbar.addAction(sim.action_delete)


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
    file_menu.addAction(sim.action_new)
    file_menu.addAction(sim.action_save)
    file_menu.addAction(sim.action_load)
    file_menu.addSeparator()
    exit_action = QAction("E&xit", sim)
    exit_action.setMenuRole(QAction.MenuRole.QuitRole)
    exit_action.triggered.connect(sim.close)
    file_menu.addAction(exit_action)

    edit_menu = menubar.addMenu("&Edit")
    edit_menu.addAction(sim.action_undo)
    edit_menu.addAction(sim.action_redo)
    edit_menu.addSeparator()
    edit_menu.addAction(sim.action_delete)

    view_menu = menubar.addMenu("&View")

    view_menu.addAction(sim.action_reset)

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
    pref_action = QAction("&Preferences...", sim)
    pref_action.setMenuRole(QAction.MenuRole.PreferencesRole)
    pref_action.triggered.connect(sim._show_settings)
    settings_menu.addAction(pref_action)
    
    settings_menu.addAction("&Global Settings...", sim._show_global_settings)

    help_menu = menubar.addMenu("&Help")
    help_menu.addAction("&How to Use", sim._show_help)
    
    about_action = QAction("&About", sim)
    about_action.setMenuRole(QAction.MenuRole.AboutRole)
    about_action.triggered.connect(sim._show_about)
    help_menu.addAction(about_action)
