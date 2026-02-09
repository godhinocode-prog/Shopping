from flask import Flask, request, jsonify
import json
import sqlite3
import os

app = Flask(__name__)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('rigs.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rigs
                 (id TEXT PRIMARY KEY, type TEXT, data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS connections
                 (id TEXT PRIMARY KEY, source TEXT, target TEXT, data TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Programming System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg-primary: #1e1e1e;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #3d3d3d;
            --text-primary: #e0e0e0;
            --text-secondary: #b0b0b0;
            --accent: #007acc;
            --accent-hover: #0098ff;
            --border: #404040;
            --success: #4caf50;
            --warning: #ff9800;
            --error: #f44336;
            --block-start: #2ecc71;
            --block-loop: #e67e22;
            --block-condition: #f39c12;
            --block-variable: #3498db;
            --block-function: #9b59b6;
            --block-output: #1abc9c;
            --block-input: #34495e;
            --block-operation: #e74c3c;
        }

        [data-theme="light"] {
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f5;
            --bg-tertiary: #e0e0e0;
            --text-primary: #212121;
            --text-secondary: #757575;
            --border: #d0d0d0;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            overflow: hidden;
        }

        #canvas-container {
            width: 100%;
            height: calc(100vh - 60px);
            position: relative;
            overflow: hidden;
            background: linear-gradient(90deg, var(--border) 1px, transparent 1px),
                        linear-gradient(var(--border) 1px, transparent 1px);
            background-size: 20px 20px;
        }

        #canvas {
            width: 100%;
            height: 100%;
            position: absolute;
            cursor: grab;
        }

        #canvas:active {
            cursor: grabbing;
        }

        svg {
            position: absolute;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
        }

        .rig {
            position: absolute;
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 8px;
            min-width: 250px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10;
            transition: box-shadow 0.2s;
        }

        .rig:hover {
            box-shadow: 0 6px 20px rgba(0,0,0,0.4);
        }

        .rig.selected {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(0, 122, 204, 0.3);
        }

        .rig-header {
            padding: 10px 12px;
            background: var(--bg-tertiary);
            border-bottom: 1px solid var(--border);
            cursor: move;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 6px 6px 0 0;
        }

        .rig-title {
            font-weight: 600;
            font-size: 14px;
            flex: 1;
        }

        .rig-btn {
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            transition: all 0.2s;
        }

        .rig-btn:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        .rig-content {
            padding: 12px;
            max-height: 400px;
            overflow-y: auto;
        }

        .rig-content::-webkit-scrollbar {
            width: 8px;
        }

        .rig-content::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }

        .rig-content::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }

        .connector {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            position: absolute;
            cursor: crosshair;
            transition: all 0.2s;
            z-index: 100;
        }

        .connector.input {
            left: -6px;
            background: var(--success);
            border: 2px solid var(--bg-secondary);
        }

        .connector.output {
            right: -6px;
            background: var(--accent);
            border: 2px solid var(--bg-secondary);
        }

        .connector:hover {
            transform: scale(1.3);
            box-shadow: 0 0 10px currentColor;
        }

        /* Code Block Styles */
        .code-block {
            position: absolute;
            border-radius: 8px;
            padding: 12px 16px;
            min-width: 180px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10;
            cursor: move;
            font-size: 13px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .code-block.selected {
            box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.5);
        }

        .code-block.start { background: var(--block-start); color: white; border-radius: 20px; }
        .code-block.end { background: var(--block-start); color: white; border-radius: 20px; }
        .code-block.loop { background: var(--block-loop); color: white; }
        .code-block.condition { background: var(--block-condition); color: white; clip-path: polygon(10% 0%, 90% 0%, 100% 50%, 90% 100%, 10% 100%, 0% 50%); }
        .code-block.variable { background: var(--block-variable); color: white; }
        .code-block.function { background: var(--block-function); color: white; }
        .code-block.output { background: var(--block-output); color: white; }
        .code-block.input { background: var(--block-input); color: white; }
        .code-block.operation { background: var(--block-operation); color: white; }

        .block-input {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            min-width: 60px;
        }

        .block-input::placeholder {
            color: rgba(255,255,255,0.6);
        }

        .block-connector {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            position: absolute;
            background: white;
            cursor: crosshair;
            z-index: 100;
        }

        .block-connector.top {
            top: -5px;
            left: 50%;
            transform: translateX(-50%);
        }

        .block-connector.bottom {
            bottom: -5px;
            left: 50%;
            transform: translateX(-50%);
        }

        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }

        .data-table th,
        .data-table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }

        .data-table th {
            background: var(--bg-tertiary);
            font-weight: 600;
            position: sticky;
            top: 0;
        }

        .data-table input {
            width: 100%;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }

        .function-input {
            margin-top: 8px;
        }

        .function-input input,
        .function-input select,
        .function-input textarea {
            width: 100%;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 6px 10px;
            border-radius: 4px;
            font-size: 12px;
            margin-top: 4px;
        }

        .function-input textarea {
            resize: vertical;
            min-height: 60px;
            font-family: 'Courier New', monospace;
        }

        .function-input label {
            font-size: 11px;
            color: var(--text-secondary);
            display: block;
        }

        .execute-btn {
            width: 100%;
            margin-top: 8px;
            padding: 8px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
        }

        .execute-btn:hover {
            background: var(--accent-hover);
        }

        .output-area {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 8px;
            margin-top: 8px;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            max-height: 150px;
            overflow-y: auto;
        }

        #bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border);
            display: flex;
            align-items: center;
            padding: 0 20px;
            gap: 10px;
            z-index: 1000;
            overflow-x: auto;
        }

        #bottom-nav::-webkit-scrollbar {
            height: 6px;
        }

        #bottom-nav::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 3px;
        }

        .nav-btn {
            padding: 8px 16px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            white-space: nowrap;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .nav-btn:hover {
            background: var(--accent);
            border-color: var(--accent);
            transform: translateY(-2px);
        }

        .nav-btn.active {
            background: var(--accent);
            border-color: var(--accent);
        }

        .mode-switcher {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px;
            z-index: 1000;
            display: flex;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }

        .mode-btn {
            padding: 6px 12px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }

        .mode-btn:hover {
            background: var(--accent);
        }

        .mode-btn.active {
            background: var(--accent);
            border-color: var(--accent-hover);
        }

        .add-column-btn {
            padding: 6px 12px;
            background: var(--success);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin: 5px 5px 8px 0;
        }

        .add-column-btn:hover {
            opacity: 0.9;
        }

        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 300px;
            overflow-y: auto;
        }

        .chat-message {
            padding: 8px 12px;
            border-radius: 6px;
            max-width: 80%;
        }

        .chat-message.user {
            background: var(--accent);
            align-self: flex-end;
            margin-left: auto;
        }

        .chat-message.assistant {
            background: var(--bg-tertiary);
            align-self: flex-start;
        }

        .chat-input-container {
            display: flex;
            gap: 8px;
            margin-top: 10px;
        }

        .chat-input-container input {
            flex: 1;
        }

        .neural-layer {
            margin: 10px 0;
        }

        .neural-node {
            display: inline-block;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #e74c3c;
            margin: 5px;
            position: relative;
        }

        .neural-node::after {
            content: attr(data-value);
            position: absolute;
            bottom: -20px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 10px;
            white-space: nowrap;
        }

        .context-menu {
            position: fixed;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 6px;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: none;
        }

        .context-menu-item {
            padding: 8px 16px;
            cursor: pointer;
            border-radius: 4px;
            font-size: 13px;
            white-space: nowrap;
        }

        .context-menu-item:hover {
            background: var(--bg-tertiary);
        }

        .type-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: 600;
            margin-left: 8px;
            background: var(--accent);
        }

        .spinner {
            border: 3px solid var(--border);
            border-top: 3px solid var(--accent);
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: inline-block;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Code Panel */
        .code-panel {
            position: fixed;
            right: 20px;
            top: 80px;
            width: 400px;
            max-height: calc(100vh - 160px);
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 999;
            display: none;
        }

        .code-panel.visible {
            display: block;
        }

        .code-panel-header {
            padding: 12px;
            background: var(--bg-tertiary);
            border-bottom: 1px solid var(--border);
            border-radius: 8px 8px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .code-panel-title {
            font-weight: 600;
            font-size: 14px;
        }

        .code-panel-content {
            padding: 12px;
            max-height: calc(100vh - 220px);
            overflow-y: auto;
        }

        .code-output {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 12px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
        }

        .copy-btn {
            padding: 6px 12px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-top: 8px;
        }

        .copy-btn:hover {
            background: var(--accent-hover);
        }

        .language-selector {
            margin-bottom: 12px;
        }

        .language-selector select {
            width: 100%;
            padding: 8px;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            border-radius: 4px;
            font-size: 12px;
        }

        /* Block Palette */
        .block-palette {
            position: fixed;
            left: 20px;
            top: 80px;
            width: 200px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 999;
            display: none;
        }

        .block-palette.visible {
            display: block;
        }

        .block-palette-header {
            padding: 12px;
            background: var(--bg-tertiary);
            border-bottom: 1px solid var(--border);
            border-radius: 8px 8px 0 0;
            font-weight: 600;
            font-size: 14px;
        }

        .block-palette-content {
            padding: 12px;
            max-height: calc(100vh - 220px);
            overflow-y: auto;
        }

        .palette-block {
            padding: 8px 12px;
            margin-bottom: 8px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            text-align: center;
            transition: all 0.2s;
        }

        .palette-block:hover {
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }

        .palette-block.start { background: var(--block-start); color: white; }
        .palette-block.loop { background: var(--block-loop); color: white; }
        .palette-block.condition { background: var(--block-condition); color: white; }
        .palette-block.variable { background: var(--block-variable); color: white; }
        .palette-block.function { background: var(--block-function); color: white; }
        .palette-block.output { background: var(--block-output); color: white; }
        .palette-block.input { background: var(--block-input); color: white; }
        .palette-block.operation { background: var(--block-operation); color: white; }
    </style>
</head>
<body>
    <div class="mode-switcher">
        <button class="mode-btn active" onclick="setTheme('dark')">🌙 Dark</button>
        <button class="mode-btn" onclick="setTheme('light')">☀️ Light</button>
        <button class="mode-btn" id="mode-toggle" onclick="toggleMode()">🎨 Rig Mode</button>
        <button class="mode-btn" onclick="clearCanvas()">🗑️ Clear</button>
        <button class="mode-btn" onclick="saveWorkspace()">💾 Save</button>
        <button class="mode-btn" onclick="loadWorkspace()">📂 Load</button>
    </div>

    <div id="canvas-container">
        <svg id="connections-svg"></svg>
        <div id="canvas"></div>
    </div>

    <div id="bottom-nav">
        <!-- Rig Mode Buttons -->
        <div id="rig-mode-nav" style="display: flex; gap: 10px;">
            <button class="nav-btn" onclick="addRig('data')"><span>📊</span> Data</button>
            <button class="nav-btn" onclick="addRig('table')"><span>📋</span> Table</button>
            <button class="nav-btn" onclick="addRig('function')"><span>⚙️</span> Function</button>
            <button class="nav-btn" onclick="addRig('llm')"><span>🤖</span> LLM</button>
            <button class="nav-btn" onclick="addRig('neural')"><span>🧠</span> Neural</button>
            <button class="nav-btn" onclick="addRig('chart')"><span>📈</span> Chart</button>
            <button class="nav-btn" onclick="addRig('database')"><span>💾</span> Database</button>
            <button class="nav-btn" onclick="addRig('custom')"><span>✨</span> Custom</button>
        </div>

        <!-- Coding Mode Buttons -->
        <div id="coding-mode-nav" style="display: none; gap: 10px;">
            <button class="nav-btn" onclick="addCodeBlock('start')"><span>🟢</span> Start</button>
            <button class="nav-btn" onclick="addCodeBlock('variable')"><span>📦</span> Variable</button>
            <button class="nav-btn" onclick="addCodeBlock('input')"><span>⌨️</span> Input</button>
            <button class="nav-btn" onclick="addCodeBlock('output')"><span>🖨️</span> Output</button>
            <button class="nav-btn" onclick="addCodeBlock('operation')"><span>➕</span> Operation</button>
            <button class="nav-btn" onclick="addCodeBlock('condition')"><span>❓</span> Condition</button>
            <button class="nav-btn" onclick="addCodeBlock('loop')"><span>🔄</span> Loop</button>
            <button class="nav-btn" onclick="addCodeBlock('function')"><span>⚙️</span> Function</button>
            <button class="nav-btn" onclick="addCodeBlock('end')"><span>🔴</span> End</button>
            <button class="nav-btn active" onclick="generateCode()"><span>⚡</span> Generate Code</button>
        </div>
    </div>

    <!-- Block Palette for Coding Mode -->
    <div id="block-palette" class="block-palette">
        <div class="block-palette-header">Building Blocks</div>
        <div class="block-palette-content">
            <div class="palette-block start" onclick="addCodeBlock('start')">🟢 Start/End</div>
            <div class="palette-block variable" onclick="addCodeBlock('variable')">📦 Variable</div>
            <div class="palette-block input" onclick="addCodeBlock('input')">⌨️ Input</div>
            <div class="palette-block output" onclick="addCodeBlock('output')">🖨️ Output</div>
            <div class="palette-block operation" onclick="addCodeBlock('operation')">➕ Operation</div>
            <div class="palette-block condition" onclick="addCodeBlock('condition')">❓ Condition</div>
            <div class="palette-block loop" onclick="addCodeBlock('loop')">🔄 Loop</div>
            <div class="palette-block function" onclick="addCodeBlock('function')">⚙️ Function</div>
        </div>
    </div>

    <!-- Code Panel -->
    <div id="code-panel" class="code-panel">
        <div class="code-panel-header">
            <div class="code-panel-title">💻 Generated Code</div>
            <button class="rig-btn" onclick="toggleCodePanel()">×</button>
        </div>
        <div class="code-panel-content">
            <div class="language-selector">
                <label style="font-size: 11px; color: var(--text-secondary); display: block; margin-bottom: 4px;">Programming Language:</label>
                <select id="language-select" onchange="generateCode()">
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="java">Java</option>
                    <option value="cpp">C++</option>
                    <option value="csharp">C#</option>
                </select>
            </div>
            <div id="code-output" class="code-output">// Click "Generate Code" to see the algorithm code here</div>
            <button class="copy-btn" onclick="copyCode()">📋 Copy Code</button>
            <button class="copy-btn" onclick="downloadCode()">💾 Download Code</button>
        </div>
    </div>

    <div id="context-menu" class="context-menu">
        <div class="context-menu-item" onclick="duplicateItem()">Duplicate</div>
        <div class="context-menu-item" onclick="deleteItem()">Delete</div>
        <div class="context-menu-item" onclick="exportItem()">Export</div>
    </div>

    <script>
        let rigs = [];
        let connections = [];
        let codeBlocks = [];
        let blockConnections = [];
        let selectedRig = null;
        let selectedBlock = null;
        let draggedRig = null;
        let draggedBlock = null;
        let canvasOffset = { x: 0, y: 0 };
        let isPanning = false;
        let panStart = { x: 0, y: 0 };
        let connectionStart = null;
        let blockConnectionStart = null;
        let rigCounter = 0;
        let blockCounter = 0;
        let autoConnect = false;
        let contextMenuTarget = null;
        let currentMode = 'rig'; // 'rig' or 'coding'

        const canvas = document.getElementById('canvas');
        const svg = document.getElementById('connections-svg');
        const contextMenu = document.getElementById('context-menu');
        const codePanel = document.getElementById('code-panel');
        const blockPalette = document.getElementById('block-palette');

        document.addEventListener('DOMContentLoaded', () => {
            loadWorkspace();
            setupEventListeners();
        });

        function setupEventListeners() {
            canvas.addEventListener('mousedown', (e) => {
                if (e.target === canvas) {
                    isPanning = true;
                    panStart = { x: e.clientX - canvasOffset.x, y: e.clientY - canvasOffset.y };
                }
            });

            document.addEventListener('mousemove', (e) => {
                if (isPanning) {
                    canvasOffset.x = e.clientX - panStart.x;
                    canvasOffset.y = e.clientY - panStart.y;
                    canvas.style.transform = `translate(${canvasOffset.x}px, ${canvasOffset.y}px)`;
                    updateConnections();
                    updateBlockConnections();
                }
            });

            document.addEventListener('mouseup', () => {
                isPanning = false;
            });

            document.addEventListener('click', (e) => {
                if (!contextMenu.contains(e.target)) {
                    contextMenu.style.display = 'none';
                }
            });

            document.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                    e.preventDefault();
                    saveWorkspace();
                }
                if (e.key === 'Delete' && (selectedRig || selectedBlock)) {
                    deleteItem();
                }
                if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
                    e.preventDefault();
                    if (currentMode === 'coding') generateCode();
                }
            });
        }

        function toggleMode() {
            currentMode = currentMode === 'rig' ? 'coding' : 'rig';
            const modeToggle = document.getElementById('mode-toggle');
            const rigNav = document.getElementById('rig-mode-nav');
            const codingNav = document.getElementById('coding-mode-nav');
            
            if (currentMode === 'coding') {
                modeToggle.textContent = '💻 Coding Mode';
                modeToggle.classList.add('active');
                rigNav.style.display = 'none';
                codingNav.style.display = 'flex';
                blockPalette.classList.add('visible');
                
                // Hide rigs, show blocks
                document.querySelectorAll('.rig').forEach(r => r.style.display = 'none');
                document.querySelectorAll('.code-block').forEach(b => b.style.display = 'flex');
            } else {
                modeToggle.textContent = '🎨 Rig Mode';
                modeToggle.classList.remove('active');
                rigNav.style.display = 'flex';
                codingNav.style.display = 'none';
                blockPalette.classList.remove('visible');
                codePanel.classList.remove('visible');
                
                // Show rigs, hide blocks
                document.querySelectorAll('.rig').forEach(r => r.style.display = 'block');
                document.querySelectorAll('.code-block').forEach(b => b.style.display = 'none');
            }
            updateConnections();
            updateBlockConnections();
        }

        // CODE BLOCKS FUNCTIONALITY
        function addCodeBlock(type) {
            const blockId = `block-${++blockCounter}`;
            const block = {
                id: blockId,
                type: type,
                x: 150 + Math.random() * 400,
                y: 100 + Math.random() * 300,
                data: getBlockDefaultData(type)
            };
            codeBlocks.push(block);
            createCodeBlockElement(block);
        }

        function getBlockDefaultData(type) {
            switch(type) {
                case 'start':
                    return { label: 'Start' };
                case 'end':
                    return { label: 'End' };
                case 'variable':
                    return { name: 'x', value: '0' };
                case 'input':
                    return { variable: 'input', prompt: 'Enter value' };
                case 'output':
                    return { expression: 'result' };
                case 'operation':
                    return { left: 'a', operator: '+', right: 'b', result: 'c' };
                case 'condition':
                    return { condition: 'x > 0' };
                case 'loop':
                    return { type: 'for', variable: 'i', start: '0', end: '10', step: '1' };
                case 'function':
                    return { name: 'myFunction', params: 'x, y' };
                default:
                    return {};
            }
        }

        function createCodeBlockElement(block) {
            const blockEl = document.createElement('div');
            blockEl.className = `code-block ${block.type}`;
            blockEl.id = block.id;
            blockEl.style.left = block.x + 'px';
            blockEl.style.top = block.y + 'px';
            blockEl.style.display = currentMode === 'coding' ? 'flex' : 'none';

            blockEl.innerHTML = getBlockContent(block);

            // Add connectors
            const topConnector = document.createElement('div');
            topConnector.className = 'block-connector top';
            topConnector.onclick = (e) => handleBlockConnectorClick(e, block.id, 'top');
            blockEl.appendChild(topConnector);

            const bottomConnector = document.createElement('div');
            bottomConnector.className = 'block-connector bottom';
            bottomConnector.onclick = (e) => handleBlockConnectorClick(e, block.id, 'bottom');
            blockEl.appendChild(bottomConnector);

            blockEl.addEventListener('mousedown', (e) => startBlockDrag(e, block));
            blockEl.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                showContextMenu(e, block);
            });
            blockEl.addEventListener('click', (e) => {
                if (e.target === blockEl || e.target.classList.contains('block-icon')) {
                    selectBlock(block.id);
                }
            });

            canvas.appendChild(blockEl);
        }

        function getBlockContent(block) {
            switch(block.type) {
                case 'start':
                    return '<div class="block-icon">🟢</div><div>Start</div>';
                case 'end':
                    return '<div class="block-icon">🔴</div><div>End</div>';
                case 'variable':
                    return `<div class="block-icon">📦</div><input class="block-input" value="${block.data.name}" onchange="updateBlockData('${block.id}', 'name', this.value)" placeholder="var"> = <input class="block-input" value="${block.data.value}" onchange="updateBlockData('${block.id}', 'value', this.value)" placeholder="value">`;
                case 'input':
                    return `<div class="block-icon">⌨️</div><input class="block-input" value="${block.data.variable}" onchange="updateBlockData('${block.id}', 'variable', this.value)" placeholder="var"> = input("<input class="block-input" value="${block.data.prompt}" onchange="updateBlockData('${block.id}', 'prompt', this.value)" placeholder="prompt">")`;
                case 'output':
                    return `<div class="block-icon">🖨️</div>print(<input class="block-input" value="${block.data.expression}" onchange="updateBlockData('${block.id}', 'expression', this.value)" placeholder="expression">)`;
                case 'operation':
                    return `<div class="block-icon">➕</div><input class="block-input" value="${block.data.result}" onchange="updateBlockData('${block.id}', 'result', this.value)" placeholder="result"> = <input class="block-input" value="${block.data.left}" onchange="updateBlockData('${block.id}', 'left', this.value)" style="width:40px"> <select class="block-input" style="width:50px" onchange="updateBlockData('${block.id}', 'operator', this.value)">
                        <option ${block.data.operator === '+' ? 'selected' : ''}>+</option>
                        <option ${block.data.operator === '-' ? 'selected' : ''}>-</option>
                        <option ${block.data.operator === '*' ? 'selected' : ''}>*</option>
                        <option ${block.data.operator === '/' ? 'selected' : ''}>/</option>
                        <option ${block.data.operator === '%' ? 'selected' : ''}>%</option>
                        <option ${block.data.operator === '**' ? 'selected' : ''}>**</option>
                    </select> <input class="block-input" value="${block.data.right}" onchange="updateBlockData('${block.id}', 'right', this.value)" style="width:40px">`;
                case 'condition':
                    return `<div class="block-icon">❓</div>if <input class="block-input" value="${block.data.condition}" onchange="updateBlockData('${block.id}', 'condition', this.value)" placeholder="condition">`;
                case 'loop':
                    return `<div class="block-icon">🔄</div>for <input class="block-input" value="${block.data.variable}" onchange="updateBlockData('${block.id}', 'variable', this.value)" style="width:30px"> in range(<input class="block-input" value="${block.data.start}" onchange="updateBlockData('${block.id}', 'start', this.value)" style="width:30px">, <input class="block-input" value="${block.data.end}" onchange="updateBlockData('${block.id}', 'end', this.value)" style="width:30px">)`;
                case 'function':
                    return `<div class="block-icon">⚙️</div>def <input class="block-input" value="${block.data.name}" onchange="updateBlockData('${block.id}', 'name', this.value)" placeholder="function">(<input class="block-input" value="${block.data.params}" onchange="updateBlockData('${block.id}', 'params', this.value)" placeholder="params">)`;
                default:
                    return 'Block';
            }
        }

        function updateBlockData(blockId, field, value) {
            const block = codeBlocks.find(b => b.id === blockId);
            if (block) {
                block.data[field] = value;
            }
        }

        function startBlockDrag(e, block) {
            if (e.target.classList.contains('block-input') || e.target.tagName === 'SELECT') return;
            draggedBlock = block;
            const blockEl = document.getElementById(block.id);
            const rect = blockEl.getBoundingClientRect();
            draggedBlock.offsetX = e.clientX - rect.left;
            draggedBlock.offsetY = e.clientY - rect.top;
            document.addEventListener('mousemove', doBlockDrag);
            document.addEventListener('mouseup', stopBlockDrag);
        }

        function doBlockDrag(e) {
            if (!draggedBlock) return;
            const blockEl = document.getElementById(draggedBlock.id);
            draggedBlock.x = e.clientX - draggedBlock.offsetX - canvasOffset.x;
            draggedBlock.y = e.clientY - draggedBlock.offsetY - canvasOffset.y;
            blockEl.style.left = draggedBlock.x + 'px';
            blockEl.style.top = draggedBlock.y + 'px';
            updateBlockConnections();
        }

        function stopBlockDrag() {
            draggedBlock = null;
            document.removeEventListener('mousemove', doBlockDrag);
            document.removeEventListener('mouseup', stopBlockDrag);
        }

        function selectBlock(blockId) {
            document.querySelectorAll('.code-block').forEach(b => b.classList.remove('selected'));
            selectedBlock = blockId;
            document.getElementById(blockId).classList.add('selected');
        }

        function handleBlockConnectorClick(e, blockId, position) {
            e.stopPropagation();
            if (!blockConnectionStart) {
                blockConnectionStart = { blockId, position };
            } else {
                if (blockConnectionStart.blockId !== blockId) {
                    createBlockConnection(blockConnectionStart.blockId, blockId);
                }
                blockConnectionStart = null;
            }
        }

        function createBlockConnection(sourceId, targetId) {
            const connId = `bconn-${sourceId}-${targetId}`;
            if (blockConnections.find(c => c.id === connId)) return;
            const connection = { id: connId, source: sourceId, target: targetId };
            blockConnections.push(connection);
            updateBlockConnections();
        }

        function updateBlockConnections() {
            if (currentMode !== 'coding') return;
            
            // Clear existing block connections from SVG
            const existingPaths = svg.querySelectorAll('path[data-type="block"]');
            existingPaths.forEach(path => path.remove());

            blockConnections.forEach(conn => {
                const sourceBlock = codeBlocks.find(b => b.id === conn.source);
                const targetBlock = codeBlocks.find(b => b.id === conn.target);
                if (!sourceBlock || !targetBlock) return;

                const sourceEl = document.getElementById(sourceBlock.id);
                const targetEl = document.getElementById(targetBlock.id);
                if (!sourceEl || !targetEl) return;

                const sourceRect = sourceEl.getBoundingClientRect();
                const targetRect = targetEl.getBoundingClientRect();
                const canvasRect = canvas.getBoundingClientRect();

                const x1 = sourceRect.left + sourceRect.width / 2 - canvasRect.left;
                const y1 = sourceRect.bottom - canvasRect.top;
                const x2 = targetRect.left + targetRect.width / 2 - canvasRect.left;
                const y2 = targetRect.top - canvasRect.top;

                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                const dy = Math.abs(y2 - y1);
                const curve = `M ${x1} ${y1} C ${x1} ${y1 + dy * 0.5}, ${x2} ${y2 - dy * 0.5}, ${x2} ${y2}`;
                path.setAttribute('d', curve);
                path.setAttribute('stroke', '#00ff88');
                path.setAttribute('stroke-width', '3');
                path.setAttribute('fill', 'none');
                path.setAttribute('opacity', '0.7');
                path.setAttribute('data-type', 'block');
                
                // Add arrow marker
                const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
                marker.setAttribute('id', `arrow-${conn.id}`);
                marker.setAttribute('markerWidth', '10');
                marker.setAttribute('markerHeight', '10');
                marker.setAttribute('refX', '5');
                marker.setAttribute('refY', '5');
                marker.setAttribute('orient', 'auto');
                const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
                polygon.setAttribute('points', '0 0, 10 5, 0 10');
                polygon.setAttribute('fill', '#00ff88');
                marker.appendChild(polygon);
                svg.appendChild(marker);
                
                path.setAttribute('marker-end', `url(#arrow-${conn.id})`);
                svg.appendChild(path);
            });
        }

        function generateCode() {
            const language = document.getElementById('language-select').value;
            const code = generateCodeFromBlocks(language);
            document.getElementById('code-output').textContent = code;
            codePanel.classList.add('visible');
        }

        function generateCodeFromBlocks(language) {
            // Sort blocks by their connections (topological sort)
            const sortedBlocks = topologicalSortBlocks();
            
            let code = '';
            let indentLevel = 0;
            const indent = () => '    '.repeat(indentLevel);

            // Language-specific templates
            const templates = {
                python: {
                    start: () => '# Algorithm Start\\n',
                    end: () => '# Algorithm End\\n',
                    variable: (b) => `${indent()}${b.data.name} = ${b.data.value}\\n`,
                    input: (b) => `${indent()}${b.data.variable} = input("${b.data.prompt}")\\n`,
                    output: (b) => `${indent()}print(${b.data.expression})\\n`,
                    operation: (b) => `${indent()}${b.data.result} = ${b.data.left} ${b.data.operator} ${b.data.right}\\n`,
                    condition: (b) => `${indent()}if ${b.data.condition}:\\n`,
                    loop: (b) => `${indent()}for ${b.data.variable} in range(${b.data.start}, ${b.data.end}):\\n`,
                    function: (b) => `${indent()}def ${b.data.name}(${b.data.params}):\\n`
                },
                javascript: {
                    start: () => '// Algorithm Start\\n',
                    end: () => '// Algorithm End\\n',
                    variable: (b) => `${indent()}let ${b.data.name} = ${b.data.value};\\n`,
                    input: (b) => `${indent()}let ${b.data.variable} = prompt("${b.data.prompt}");\\n`,
                    output: (b) => `${indent()}console.log(${b.data.expression});\\n`,
                    operation: (b) => `${indent()}let ${b.data.result} = ${b.data.left} ${b.data.operator} ${b.data.right};\\n`,
                    condition: (b) => `${indent()}if (${b.data.condition}) {\\n`,
                    loop: (b) => `${indent()}for (let ${b.data.variable} = ${b.data.start}; ${b.data.variable} < ${b.data.end}; ${b.data.variable}++) {\\n`,
                    function: (b) => `${indent()}function ${b.data.name}(${b.data.params}) {\\n`
                },
                java: {
                    start: () => 'public class Algorithm {\\n    public static void main(String[] args) {\\n',
                    end: () => '    }\\n}\\n',
                    variable: (b) => `${indent()}    int ${b.data.name} = ${b.data.value};\\n`,
                    input: (b) => `${indent()}    Scanner scanner = new Scanner(System.in);\\n${indent()}    System.out.println("${b.data.prompt}");\\n${indent()}    String ${b.data.variable} = scanner.nextLine();\\n`,
                    output: (b) => `${indent()}    System.out.println(${b.data.expression});\\n`,
                    operation: (b) => `${indent()}    int ${b.data.result} = ${b.data.left} ${b.data.operator} ${b.data.right};\\n`,
                    condition: (b) => `${indent()}    if (${b.data.condition}) {\\n`,
                    loop: (b) => `${indent()}    for (int ${b.data.variable} = ${b.data.start}; ${b.data.variable} < ${b.data.end}; ${b.data.variable}++) {\\n`,
                    function: (b) => `${indent()}    public static void ${b.data.name}(${b.data.params}) {\\n`
                },
                cpp: {
                    start: () => '#include <iostream>\\nusing namespace std;\\n\\nint main() {\\n',
                    end: () => '    return 0;\\n}\\n',
                    variable: (b) => `${indent()}    int ${b.data.name} = ${b.data.value};\\n`,
                    input: (b) => `${indent()}    cout << "${b.data.prompt}";\\n${indent()}    cin >> ${b.data.variable};\\n`,
                    output: (b) => `${indent()}    cout << ${b.data.expression} << endl;\\n`,
                    operation: (b) => `${indent()}    int ${b.data.result} = ${b.data.left} ${b.data.operator} ${b.data.right};\\n`,
                    condition: (b) => `${indent()}    if (${b.data.condition}) {\\n`,
                    loop: (b) => `${indent()}    for (int ${b.data.variable} = ${b.data.start}; ${b.data.variable} < ${b.data.end}; ${b.data.variable}++) {\\n`,
                    function: (b) => `${indent()}    void ${b.data.name}(${b.data.params}) {\\n`
                },
                csharp: {
                    start: () => 'using System;\\n\\nclass Program {\\n    static void Main() {\\n',
                    end: () => '    }\\n}\\n',
                    variable: (b) => `${indent()}        int ${b.data.name} = ${b.data.value};\\n`,
                    input: (b) => `${indent()}        Console.WriteLine("${b.data.prompt}");\\n${indent()}        string ${b.data.variable} = Console.ReadLine();\\n`,
                    output: (b) => `${indent()}        Console.WriteLine(${b.data.expression});\\n`,
                    operation: (b) => `${indent()}        int ${b.data.result} = ${b.data.left} ${b.data.operator} ${b.data.right};\\n`,
                    condition: (b) => `${indent()}        if (${b.data.condition}) {\\n`,
                    loop: (b) => `${indent()}        for (int ${b.data.variable} = ${b.data.start}; ${b.data.variable} < ${b.data.end}; ${b.data.variable}++) {\\n`,
                    function: (b) => `${indent()}        static void ${b.data.name}(${b.data.params}) {\\n`
                }
            };

            const template = templates[language] || templates.python;

            sortedBlocks.forEach((block, index) => {
                if (template[block.type]) {
                    code += template[block.type](block);
                    
                    // Increase indent for blocks that need it
                    if (['condition', 'loop', 'function'].includes(block.type)) {
                        indentLevel++;
                    }
                    
                    // Decrease indent when needed (simplified logic)
                    const nextBlock = sortedBlocks[index + 1];
                    if (nextBlock && !hasConnection(block.id, nextBlock.id) && indentLevel > 0) {
                        if (language === 'javascript' || language === 'java' || language === 'cpp' || language === 'csharp') {
                            code += `${indent()}}\\n`;
                        }
                        indentLevel = Math.max(0, indentLevel - 1);
                    }
                }
            });

            // Close any remaining blocks
            while (indentLevel > 0) {
                indentLevel--;
                if (language === 'javascript' || language === 'java' || language === 'cpp' || language === 'csharp') {
                    code += `${indent()}}\\n`;
                }
            }

            if (sortedBlocks.length === 0) {
                code = '// No blocks connected. Add blocks and connect them to generate code.\\n';
            }

            return code;
        }

        function topologicalSortBlocks() {
            // Find start block
            const startBlock = codeBlocks.find(b => b.type === 'start');
            if (!startBlock) return codeBlocks;

            const sorted = [];
            const visited = new Set();

            function visit(blockId) {
                if (visited.has(blockId)) return;
                visited.add(blockId);
                
                const block = codeBlocks.find(b => b.id === blockId);
                if (block) {
                    sorted.push(block);
                    
                    // Find all blocks connected from this one
                    const nextConnections = blockConnections.filter(c => c.source === blockId);
                    nextConnections.forEach(conn => visit(conn.target));
                }
            }

            visit(startBlock.id);
            return sorted;
        }

        function hasConnection(sourceId, targetId) {
            return blockConnections.some(c => c.source === sourceId && c.target === targetId);
        }

        function copyCode() {
            const codeText = document.getElementById('code-output').textContent;
            navigator.clipboard.writeText(codeText).then(() => {
                alert('Code copied to clipboard!');
            });
        }

        function downloadCode() {
            const language = document.getElementById('language-select').value;
            const extensions = {
                python: 'py',
                javascript: 'js',
                java: 'java',
                cpp: 'cpp',
                csharp: 'cs'
            };
            const codeText = document.getElementById('code-output').textContent;
            const blob = new Blob([codeText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `algorithm.${extensions[language]}`;
            a.click();
        }

        function toggleCodePanel() {
            codePanel.classList.toggle('visible');
        }

        // RIG MODE FUNCTIONALITY (from previous version)
        function addRig(type) {
            const rigId = `rig-${++rigCounter}`;
            const rig = {
                id: rigId,
                type: type,
                x: 100 + Math.random() * 300,
                y: 100 + Math.random() * 200,
                data: getRigDefaultData(type)
            };
            rigs.push(rig);
            createRigElement(rig);
            saveToBackend(rig);
        }

        function getRigDefaultData(type) {
            switch(type) {
                case 'table':
                    return { columns: ['Col 1', 'Col 2', 'Col 3'], rows: [['', '', ''], ['', '', '']] };
                case 'function':
                    return { functionType: 'sum', code: '// Custom function\\nreturn input;' };
                case 'neural':
                    return { layers: [4, 6, 4, 2], activation: 'relu' };
                case 'llm':
                    return { messages: [], model: 'gpt-4', temperature: 0.7 };
                case 'chart':
                    return { chartType: 'line', data: [] };
                case 'database':
                    return { tables: [], queries: [] };
                default:
                    return {};
            }
        }

        function createRigElement(rig) {
            const rigEl = document.createElement('div');
            rigEl.className = 'rig';
            rigEl.id = rig.id;
            rigEl.style.left = rig.x + 'px';
            rigEl.style.top = rig.y + 'px';
            rigEl.style.display = currentMode === 'rig' ? 'block' : 'none';

            rigEl.innerHTML = `
                <div class="rig-header">
                    <div class="rig-title">${getTypeIcon(rig.type)} ${rig.type}<span class="type-badge">${rig.type.toUpperCase()}</span></div>
                    <div><button class="rig-btn" onclick="minimizeRig('${rig.id}')">−</button>
                    <button class="rig-btn" onclick="removeRig('${rig.id}')">×</button></div>
                </div>
                <div class="rig-content" id="${rig.id}-content">${getRigContent(rig)}</div>
            `;

            const inputConnector = document.createElement('div');
            inputConnector.className = 'connector input';
            inputConnector.style.top = '20px';
            inputConnector.onclick = (e) => handleConnectorClick(e, rig.id, 'input');
            rigEl.appendChild(inputConnector);

            const outputConnector = document.createElement('div');
            outputConnector.className = 'connector output';
            outputConnector.style.top = '20px';
            outputConnector.onclick = (e) => handleConnectorClick(e, rig.id, 'output');
            rigEl.appendChild(outputConnector);

            const header = rigEl.querySelector('.rig-header');
            header.addEventListener('mousedown', (e) => startDrag(e, rig));

            rigEl.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                showContextMenu(e, rig);
            });

            rigEl.addEventListener('click', () => selectRig(rig.id));
            canvas.appendChild(rigEl);
        }

        function getRigContent(rig) {
            switch(rig.type) {
                case 'table': return createTableContent(rig);
                case 'function': return createFunctionContent(rig);
                case 'neural': return createNeuralContent(rig);
                case 'llm': return createLLMContent(rig);
                case 'chart': return createChartContent(rig);
                case 'database': return createDatabaseContent(rig);
                case 'data': return createDataContent(rig);
                default: return '<p>Custom Rig - Add your content here</p>';
            }
        }

        function createTableContent(rig) {
            let html = '<div>';
            html += `<button class="add-column-btn" onclick="addColumn('${rig.id}')">+ Column</button>`;
            html += `<button class="add-column-btn" onclick="addRow('${rig.id}')">+ Row</button></div>`;
            html += '<table class="data-table"><thead><tr>';
            rig.data.columns.forEach((col, i) => {
                html += `<th><input value="${col}" onchange="updateColumnName('${rig.id}', ${i}, this.value)" /></th>`;
            });
            html += '</tr></thead><tbody>';
            rig.data.rows.forEach((row, ri) => {
                html += '<tr>';
                row.forEach((cell, ci) => {
                    html += `<td><input value="${cell}" onchange="updateCell('${rig.id}', ${ri}, ${ci}, this.value)" /></td>`;
                });
                html += '</tr>';
            });
            html += '</tbody></table>';
            return html;
        }

        function createFunctionContent(rig) {
            return `
                <div class="function-input"><label>Function Type</label>
                <select onchange="updateFunctionType('${rig.id}', this.value)">
                    <option value="sum">Sum</option><option value="average">Average</option>
                    <option value="filter">Filter</option><option value="map">Map</option>
                    <option value="custom">Custom</option>
                </select></div>
                <div class="function-input"><label>Custom Code (JavaScript)</label>
                <textarea onchange="updateFunctionCode('${rig.id}', this.value)">${rig.data.code}</textarea></div>
                <button class="execute-btn" onclick="executeFunction('${rig.id}')">Execute Function</button>
                <div class="output-area" id="${rig.id}-output">Output will appear here...</div>
            `;
        }

        function createNeuralContent(rig) {
            let html = '<div class="function-input"><label>Network Architecture (comma-separated)</label>';
            html += `<input value="${rig.data.layers.join(',')}" onchange="updateNeuralLayers('${rig.id}', this.value)" /></div>`;
            rig.data.layers.forEach((count, i) => {
                html += `<div class="neural-layer"><small>Layer ${i + 1} (${count} nodes)</small><br>`;
                for(let j = 0; j < Math.min(count, 8); j++) {
                    html += `<div class="neural-node" data-value="${(Math.random()).toFixed(2)}"></div>`;
                }
                if(count > 8) html += `<span>... +${count - 8} more</span>`;
                html += '</div>';
            });
            html += `<button class="execute-btn" onclick="trainNetwork('${rig.id}')">Train Network</button>`;
            return html;
        }

        function createLLMContent(rig) {
            let html = `<div class="chat-container" id="${rig.id}-chat">`;
            rig.data.messages.forEach(msg => {
                html += `<div class="chat-message ${msg.role}">${msg.content}</div>`;
            });
            html += '</div><div class="chat-input-container">';
            html += `<input type="text" id="${rig.id}-input" placeholder="Type a message..." onkeypress="if(event.key==='Enter') sendLLMMessage('${rig.id}')" />`;
            html += `<button class="execute-btn" style="margin:0;width:auto;padding:6px 12px;" onclick="sendLLMMessage('${rig.id}')">Send</button></div>`;
            return html;
        }

        function createChartContent(rig) {
            return `<div class="function-input"><label>Chart Type</label>
                <select onchange="updateChartType('${rig.id}', this.value)">
                    <option value="line">Line Chart</option><option value="bar">Bar Chart</option>
                    <option value="pie">Pie Chart</option><option value="scatter">Scatter Plot</option>
                </select></div>
                <div style="width:100%;height:150px;background:var(--bg-primary);border-radius:4px;display:flex;align-items:center;justify-content:center;">
                    Chart will render here
                </div>`;
        }

        function createDatabaseContent(rig) {
            return `<div class="function-input"><label>SQL Query</label>
                <textarea placeholder="SELECT * FROM table_name"></textarea></div>
                <button class="execute-btn" onclick="executeQuery('${rig.id}')">Run Query</button>
                <div class="output-area" id="${rig.id}-query-output">Results will appear here...</div>`;
        }

        function createDataContent(rig) {
            return `<div class="function-input"><label>Data Source</label>
                <input type="text" placeholder="Enter data or URL" /></div>
                <div class="function-input"><label>Format</label>
                <select><option>JSON</option><option>CSV</option><option>XML</option></select></div>
                <button class="execute-btn" onclick="loadData('${rig.id}')">Load Data</button>`;
        }

        function startDrag(e, rig) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
            draggedRig = rig;
            const rigEl = document.getElementById(rig.id);
            const rect = rigEl.getBoundingClientRect();
            draggedRig.offsetX = e.clientX - rect.left;
            draggedRig.offsetY = e.clientY - rect.top;
            document.addEventListener('mousemove', doDrag);
            document.addEventListener('mouseup', stopDrag);
        }

        function doDrag(e) {
            if (!draggedRig) return;
            const rigEl = document.getElementById(draggedRig.id);
            draggedRig.x = e.clientX - draggedRig.offsetX - canvasOffset.x;
            draggedRig.y = e.clientY - draggedRig.offsetY - canvasOffset.y;
            rigEl.style.left = draggedRig.x + 'px';
            rigEl.style.top = draggedRig.y + 'px';
            updateConnections();
        }

        function stopDrag() {
            if (draggedRig) saveToBackend(draggedRig);
            draggedRig = null;
            document.removeEventListener('mousemove', doDrag);
            document.removeEventListener('mouseup', stopDrag);
        }

        function handleConnectorClick(e, rigId, type) {
            e.stopPropagation();
            if (!connectionStart) {
                connectionStart = { rigId, type };
            } else {
                if (connectionStart.rigId !== rigId) {
                    createConnection(connectionStart.rigId, rigId);
                }
                connectionStart = null;
            }
        }

        function createConnection(sourceId, targetId) {
            const connId = `conn-${sourceId}-${targetId}`;
            if (connections.find(c => c.id === connId)) return;
            const connection = { id: connId, source: sourceId, target: targetId };
            connections.push(connection);
            updateConnections();
            saveConnectionToBackend(connection);
        }

        function updateConnections() {
            if (currentMode !== 'rig') return;
            
            const existingPaths = svg.querySelectorAll('path[data-type="rig"]');
            existingPaths.forEach(path => path.remove());

            connections.forEach(conn => {
                const sourceRig = rigs.find(r => r.id === conn.source);
                const targetRig = rigs.find(r => r.id === conn.target);
                if (!sourceRig || !targetRig) return;
                const sourceEl = document.getElementById(sourceRig.id);
                const targetEl = document.getElementById(targetRig.id);
                if (!sourceEl || !targetEl) return;
                const sourceRect = sourceEl.getBoundingClientRect();
                const targetRect = targetEl.getBoundingClientRect();
                const canvasRect = canvas.getBoundingClientRect();
                const x1 = sourceRect.right - canvasRect.left;
                const y1 = sourceRect.top - canvasRect.top + 20;
                const x2 = targetRect.left - canvasRect.left;
                const y2 = targetRect.top - canvasRect.top + 20;
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                const dx = Math.abs(x2 - x1);
                const curve = `M ${x1} ${y1} C ${x1 + dx * 0.5} ${y1}, ${x2 - dx * 0.5} ${y2}, ${x2} ${y2}`;
                path.setAttribute('d', curve);
                path.setAttribute('stroke', '#007acc');
                path.setAttribute('stroke-width', '2');
                path.setAttribute('fill', 'none');
                path.setAttribute('opacity', '0.6');
                path.setAttribute('data-type', 'rig');
                svg.appendChild(path);
            });
        }

        function removeRig(rigId) {
            const index = rigs.findIndex(r => r.id === rigId);
            if (index > -1) {
                rigs.splice(index, 1);
                document.getElementById(rigId).remove();
                connections = connections.filter(c => c.source !== rigId && c.target !== rigId);
                updateConnections();
                fetch('/api/rigs', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: rigId }) });
            }
        }

        function selectRig(rigId) {
            document.querySelectorAll('.rig').forEach(r => r.classList.remove('selected'));
            selectedRig = rigId;
            document.getElementById(rigId).classList.add('selected');
        }

        function minimizeRig(rigId) {
            const content = document.getElementById(rigId + '-content');
            content.style.display = content.style.display === 'none' ? 'block' : 'none';
        }

        function updateRigContent(rigId) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                document.getElementById(rigId + '-content').innerHTML = getRigContent(rig);
                saveToBackend(rig);
            }
        }

        function addColumn(rigId) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.columns.push(`Col ${rig.data.columns.length + 1}`);
                rig.data.rows.forEach(row => row.push(''));
                updateRigContent(rigId);
            }
        }

        function addRow(rigId) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.rows.push(new Array(rig.data.columns.length).fill(''));
                updateRigContent(rigId);
            }
        }

        function updateColumnName(rigId, colIndex, value) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.columns[colIndex] = value;
                saveToBackend(rig);
            }
        }

        function updateCell(rigId, rowIndex, colIndex, value) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.rows[rowIndex][colIndex] = value;
                saveToBackend(rig);
            }
        }

        function updateFunctionType(rigId, type) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.functionType = type;
                saveToBackend(rig);
            }
        }

        function updateFunctionCode(rigId, code) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.code = code;
                saveToBackend(rig);
            }
        }

        function executeFunction(rigId) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                const output = document.getElementById(rigId + '-output');
                output.innerHTML = '<div class="spinner"></div> Executing...';
                const inputConnections = connections.filter(c => c.target === rigId);
                const inputData = inputConnections.map(c => {
                    const sourceRig = rigs.find(r => r.id === c.source);
                    return sourceRig ? sourceRig.data : null;
                });
                try {
                    const func = new Function('input', rig.data.code);
                    const result = func(inputData);
                    output.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
                } catch(e) {
                    output.innerHTML = `<span style="color:var(--error)">Error: ${e.message}</span>`;
                }
            }
        }

        function updateNeuralLayers(rigId, value) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.layers = value.split(',').map(n => parseInt(n.trim()));
                updateRigContent(rigId);
            }
        }

        function trainNetwork(rigId) {
            alert('Neural network training initiated for ' + rigId);
        }

        function sendLLMMessage(rigId) {
            const rig = rigs.find(r => r.id === rigId);
            const input = document.getElementById(rigId + '-input');
            if (rig && input.value.trim()) {
                rig.data.messages.push({ role: 'user', content: input.value });
                setTimeout(() => {
                    rig.data.messages.push({ role: 'assistant', content: 'This is a simulated AI response. Connect to actual LLM API for real responses.' });
                    updateRigContent(rigId);
                }, 1000);
                updateRigContent(rigId);
                input.value = '';
            }
        }

        function updateChartType(rigId, type) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.chartType = type;
                saveToBackend(rig);
            }
        }

        function executeQuery(rigId) {
            alert('Database query executed for ' + rigId);
        }

        function loadData(rigId) {
            alert('Data loaded for ' + rigId);
        }

        function showContextMenu(e, item) {
            contextMenuTarget = item;
            contextMenu.style.left = e.clientX + 'px';
            contextMenu.style.top = e.clientY + 'px';
            contextMenu.style.display = 'block';
        }

        function duplicateItem() {
            if (currentMode === 'rig' && contextMenuTarget && contextMenuTarget.type) {
                const original = rigs.find(r => r.id === contextMenuTarget.id);
                if (original) {
                    const newRig = { ...original, id: `rig-${++rigCounter}`, x: original.x + 30, y: original.y + 30 };
                    rigs.push(newRig);
                    createRigElement(newRig);
                    saveToBackend(newRig);
                }
            } else if (currentMode === 'coding' && contextMenuTarget) {
                const original = codeBlocks.find(b => b.id === contextMenuTarget.id);
                if (original) {
                    const newBlock = { ...original, id: `block-${++blockCounter}`, x: original.x + 30, y: original.y + 30 };
                    codeBlocks.push(newBlock);
                    createCodeBlockElement(newBlock);
                }
            }
            contextMenu.style.display = 'none';
        }

        function deleteItem() {
            if (currentMode === 'rig' && (contextMenuTarget || selectedRig)) {
                const id = contextMenuTarget?.id || selectedRig;
                removeRig(id);
            } else if (currentMode === 'coding' && (contextMenuTarget || selectedBlock)) {
                const id = contextMenuTarget?.id || selectedBlock;
                const index = codeBlocks.findIndex(b => b.id === id);
                if (index > -1) {
                    codeBlocks.splice(index, 1);
                    document.getElementById(id).remove();
                    blockConnections = blockConnections.filter(c => c.source !== id && c.target !== id);
                    updateBlockConnections();
                }
            }
            contextMenu.style.display = 'none';
        }

        function exportItem() {
            if (contextMenuTarget) {
                const data = JSON.stringify(contextMenuTarget, null, 2);
                const blob = new Blob([data], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${contextMenuTarget.id}.json`;
                a.click();
            }
            contextMenu.style.display = 'none';
        }

        function saveWorkspace() {
            localStorage.setItem('workspace', JSON.stringify({ rigs, connections, codeBlocks, blockConnections }));
            rigs.forEach(saveToBackend);
            connections.forEach(saveConnectionToBackend);
            alert('Workspace saved successfully!');
        }

        function loadWorkspace() {
            fetch('/api/rigs').then(r => r.json()).then(data => {
                rigs = data;
                canvas.innerHTML = '';
                rigs.forEach(createRigElement);
                return fetch('/api/connections');
            }).then(r => r.json()).then(data => {
                connections = data;
                updateConnections();
            }).catch(err => {
                const saved = localStorage.getItem('workspace');
                if (saved) {
                    const data = JSON.parse(saved);
                    rigs = data.rigs || [];
                    connections = data.connections || [];
                    codeBlocks = data.codeBlocks || [];
                    blockConnections = data.blockConnections || [];
                    canvas.innerHTML = '';
                    rigs.forEach(createRigElement);
                    codeBlocks.forEach(createCodeBlockElement);
                    updateConnections();
                    updateBlockConnections();
                }
            });
        }

        function clearCanvas() {
            if (confirm('Clear all items?')) {
                if (currentMode === 'rig') {
                    rigs = [];
                    connections = [];
                    document.querySelectorAll('.rig').forEach(r => r.remove());
                } else {
                    codeBlocks = [];
                    blockConnections = [];
                    document.querySelectorAll('.code-block').forEach(b => b.remove());
                }
                svg.innerHTML = '';
            }
        }

        function saveToBackend(rig) {
            fetch('/api/rigs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(rig) });
        }

        function saveConnectionToBackend(connection) {
            fetch('/api/connections', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(connection) });
        }

        function setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }

        function getTypeIcon(type) {
            const icons = { data: '📊', table: '📋', function: '⚙️', llm: '🤖', neural: '🧠', chart: '📈', database: '💾', custom: '✨' };
            return icons[type] || '📦';
        }

        setTimeout(() => {
            if (rigs.length === 0 && codeBlocks.length === 0) {
                addRig('data');
                addRig('function');
            }
        }, 500);
    </script>
</body>
</html>'''

@app.route('/api/rigs', methods=['GET', 'POST', 'DELETE'])
def handle_rigs():
    if request.method == 'POST':
        data = request.json
        conn = sqlite3.connect('rigs.db')
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO rigs VALUES (?, ?, ?)',
                  (data['id'], data['type'], json.dumps(data)))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    elif request.method == 'DELETE':
        rig_id = request.json.get('id')
        conn = sqlite3.connect('rigs.db')
        c = conn.cursor()
        c.execute('DELETE FROM rigs WHERE id = ?', (rig_id,))
        c.execute('DELETE FROM connections WHERE source LIKE ? OR target LIKE ?', 
                  (f'{rig_id}%', f'{rig_id}%'))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    else:
        conn = sqlite3.connect('rigs.db')
        c = conn.cursor()
        c.execute('SELECT data FROM rigs')
        rigs = [json.loads(row[0]) for row in c.fetchall()]
        conn.close()
        return jsonify(rigs)

@app.route('/api/connections', methods=['GET', 'POST', 'DELETE'])
def handle_connections():
    if request.method == 'POST':
        data = request.json
        conn = sqlite3.connect('rigs.db')
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO connections VALUES (?, ?, ?, ?)',
                  (data['id'], data['source'], data['target'], json.dumps(data)))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    elif request.method == 'DELETE':
        conn_id = request.json.get('id')
        conn = sqlite3.connect('rigs.db')
        c = conn.cursor()
        c.execute('DELETE FROM connections WHERE id = ?', (conn_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    else:
        conn = sqlite3.connect('rigs.db')
        c = conn.cursor()
        c.execute('SELECT data FROM connections')
        connections = [json.loads(row[0]) for row in c.fetchall()]
        conn.close()
        return jsonify(connections)

@app.route('/api/execute', methods=['POST'])
def execute_function():
    data = request.json
    function_type = data.get('function')
    params = data.get('params', {})
    result = {'status': 'success', 'output': f'Executed {function_type} with params: {params}'}
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5400))
    app.run(host="0.0.0.0", port=port)
