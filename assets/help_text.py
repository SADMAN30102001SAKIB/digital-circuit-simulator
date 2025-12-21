HELP_TEXT = """
            <h2>🎮 Controls</h2>

            <h3>Mouse Interaction</h3>
            <table>
            <tr><td><b>Left-click drag</b></td><td>Pan the canvas</td></tr>
            <tr><td><b>Scroll wheel</b></td><td>Zoom in/out to focus on details</td></tr>
            <tr><td><b>Left-click</b></td><td>Select a component or annotation</td></tr>
            <tr><td><b>Double-click INPUT</b></td><td>Toggle Switch ON/OFF</td></tr>
            <tr><td><b>Pin Connection</b></td><td>Click an output (right) then an input (left) to wire</td></tr>
            <tr><td><b>Wire Waypoints</b></td><td>Click empty space while wiring to add corners</td></tr>
            <tr><td><b>Right-click Pin</b></td><td>Remove all wires connected to that pin</td></tr>
            </table>

            <h3>Keyboard Shortcuts</h3>
            <table>
            <tr><td><b>Ctrl + N / O</b></td><td>New Circuit / Load Circuit</td></tr>
            <tr><td><b>Ctrl + S</b></td><td>Save Circuit (YAML format)</td></tr>
            <tr><td><b>Ctrl + Z / Y</b></td><td>Undo / Redo (with history limit)</td></tr>
            <tr><td><b>Delete / Backspace</b></td><td>Delete selected items</td></tr>
            <tr><td><b>Q / E</b></td><td>Rotate selection CCW / CW</td></tr>
            <tr><td><b>R / G</b></td><td>Reset Zoom / Toggle Grid</td></tr>
            <tr><td><b>C / P</b></td><td>Show Component Library / Property Panel</td></tr>
            <tr><td><b>Escape</b></td><td>Cancel current action or wire</td></tr>
            </table>

            <h3>🛠️ Advanced Features</h3>

            <h4>Truth Table Generator</h4>
            <p>Analyze your logic automatically! Select any <b>Output LED</b> and click "Generate Truth Table" in the Property Panel. The app will trace all influencing inputs and compute every possible state combo.</p>
            <ul>
                <li><b>Virtual Loading</b>: Handles millions of rows instantly.</li>
                <li><b>CSV Export</b>: Save your results for external analysis.</li>
            </ul>

            <h4>Smart Component Naming</h4>
            <p>New <b>Input Switches</b> are auto-labeled (e.g., <i>IN1, IN2</i>). These labels appear on the canvas and serve as headers in your truth tables.</p>

            <h4>Component Configuration</h4>
            <p>Use the <b>Property Panel</b> to customize your circuit:</p>
            <ul>
                <li><b>Gates</b>: Change number of inputs for AND/OR/XOR gates.</li>
                <li><b>MUX/DEMUX</b>: Adjust select bits to scale from 2-to-1 MUX up to 1-to-16 DEMUX.</li>
                <li><b>Encoder/Decoder</b>: Scale from 4-to-2 Encoders up to 4-to-16 Decoders.</li>
                <li><b>Annotations</b>: Add Text, Rectangles, and Circles to document your design.</li>
            </ul>

            <h3>⚙️ Settings</h3>
            <p>Configure <b>Preferences</b> for the current circuit (Grid, FPS, Canvas size). Use <b>Global Settings</b> to set your application-wide <b>Undo History Limit</b> (10-200 steps).</p>
        """

ABOUT_TEXT = """
<h2>Circuit Playground Pro</h2>

<p>A professional-grade visual logic circuit simulator designed for precision and performance.</p>

<p><b>Features:</b></p>
<ul>
    <li>High-performance simulation engine</li>
    <li>Virtual Truth Table Generator with CSV export</li>
    <li>Robust Undo/Redo system with branching support</li>
    <li>YAML serialization for compact, readable saves</li>
</ul>

<p><b>Version:</b> 3.1.0 (Advanced Audit Edition)</p>
"""
