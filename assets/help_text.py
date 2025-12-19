HELP_TEXT = """
            <h2>🎮 Controls</h2>

            <h3>Mouse</h3>
            <table>
            <tr><td><b>Left-click drag</b></td><td>Pan the canvas</td></tr>
            <tr><td><b>Scroll wheel</b></td><td>Zoom in/out</td></tr>
            <tr><td><b>Click component</b></td><td>Select it</td></tr>
            <tr><td><b>Drag component</b></td><td>Move it</td></tr>
            <tr><td><b>Double-click INPUT</b></td><td>Toggle ON/OFF</td></tr>
            <tr><td><b>Click output pin</b></td><td>Start wire</td></tr>
            <tr><td><b>Click input pin</b></td><td>Complete wire</td></tr>
            <tr><td><b>Click while wiring</b></td><td>Add waypoint</td></tr>
            <tr><td><b>Right-click input pin</b></td><td>Remove wire</td></tr>
            </table>

            <h3>Keyboard Shortcuts</h3>
            <table>
            <tr><td><b>Ctrl+N</b></td><td>New circuit</td></tr>
            <tr><td><b>Ctrl+S</b></td><td>Save circuit</td></tr>
            <tr><td><b>Ctrl+L</b></td><td>Load circuit</td></tr>
            <tr><td><b>Ctrl+Z</b></td><td>Undo</td></tr>
            <tr><td><b>Ctrl+Y</b></td><td>Redo</td></tr>
            <tr><td><b>Delete</b></td><td>Delete selected</td></tr>
            <tr><td><b>Q</b></td><td>Rotate counter-clockwise</td></tr>
            <tr><td><b>E</b></td><td>Rotate clockwise</td></tr>
            <tr><td><b>R</b></td><td>Reset view</td></tr>
            <tr><td><b>G</b></td><td>Toggle grid</td></tr>
            <tr><td><b>C</b></td><td>Toggle component library</td></tr>
            <tr><td><b>P</b></td><td>Toggle properties panel</td></tr>
            <tr><td><b>Escape</b></td><td>Cancel wire connection</td></tr>
            </table>

            <h3>Building Circuits</h3>
            <ol>
            <li>Click a component in the library to add it</li>
            <li>Drag components to position them</li>
            <li>Click an output pin (right side), then click an input pin (left side) to connect</li>
            <li>Double-click INPUT switches to toggle them</li>
            <li>Watch the LED respond to your logic!</li>
            </ol>

            <h3>Settings</h3>
            <p>Go to <b>Settings > Preferences</b> to configure:</p>
            <ul>
            <li><b>Canvas Size</b>: Adjust workspace dimensions</li>
            <li><b>Grid Size</b>: Change snap-to-grid spacing</li>
            <li><b>Simulation FPS</b>: Control simulation speed</li>
            </ul>

            <p>For application-wide options, open <b>Settings > Global Settings</b>:</p>
            <ul>
            <li><b>Undo/Redo History Limit</b>: Set how many undo/redo steps are kept (10-200). Increasing this lets you go back further but may use more memory; a value like 50-100 is a good balance.</li>
            </ul>
        """

ABOUT_TEXT = """
<h2>Circuit Playground Pro</h2>

<p>A visual logic circuit simulator.</p>

<p>Build and test digital logic circuits with gates like AND, OR, NOT, XOR, NAND, NOR, XNOR, MUX, DEMUX, Encoder, and Decoder.</p>

<p><b>Version:</b> 3.0.0</p>
"""
