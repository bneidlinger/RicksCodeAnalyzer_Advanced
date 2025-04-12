#!/usr/bin/env python3
# Rick's Code Analyzer - Advanced Integrated Version
# Combines the original analyzer with advanced analysis and reporting capabilities

import os
import tkinter as tk
from tkinter import filedialog, messagebox, font, ttk
import threading
from datetime import datetime
import time
from collections import defaultdict, Counter
import random
import webbrowser  # Needed for opening report
import platform    # Needed for _open_report_in_browser
import subprocess  # Needed for _open_report_in_browser
import traceback # For detailed error reporting

# Import necessary packages for HTML report
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_for_filename, guess_lexer
    from pygments.formatters import HtmlFormatter
    from pygments.util import ClassNotFound
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

try:
    import jinja2
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

REPORT_PACKAGES_AVAILABLE = all([PYGMENTS_AVAILABLE, JINJA2_AVAILABLE, CHARDET_AVAILABLE])

# Import advanced modules if available
try:
    from advanced_analyzer import AdvancedCodeAnalyzer
    from advanced_reporter import AdvancedReporter
    ADVANCED_MODULES_AVAILABLE = True
except ImportError:
    ADVANCED_MODULES_AVAILABLE = False
    AdvancedCodeAnalyzer = None # Define as None if not available
    AdvancedReporter = None     # Define as None if not available

# Import fun module if available
try:
    from fun_analyzer import FunCodeAnalyzer
    FUN_MODULE_AVAILABLE = True
except ImportError:
    FUN_MODULE_AVAILABLE = False
    FunCodeAnalyzer = None # Define as None if not available

# Import extras module if available
try:
    from project_extras import run_safety_check, prepare_graph_data
    EXTRAS_MODULE_AVAILABLE = True
except ImportError:
    EXTRAS_MODULE_AVAILABLE = False
    run_safety_check = None # Define as None if not available
    prepare_graph_data = None # Define as None if not available

MAX_FILE_LINES = 100000 # Maximum lines of code for a file to be analyzed

# Retro color scheme
COLORS = {
    'bg': '#000000',  # Black background
    'text': '#00FF00',  # Bright green text
    'highlight': '#39FF14',  # Neon green highlight
    'warning': '#FF6000',  # Orange warning
    'error': '#FF0000',  # Red error
    'accent1': '#00FFFF',  # Cyan accent
    'accent2': '#FF00FF',  # Magenta accent
    'button': '#222222',  # Dark grey button
    'button_hover': '#444444',  # Light grey button hover
}

# Rick quotes for analysis
RICK_QUOTES = [
    "Wubba lubba dub dub! Your code's a *burp* mess!",
    "I'm not saying your code is bad, but the garbage collector wants its *burp* job back.",
    "Your code is like a Meeseeks box. Push the button and everything breaks.",
    "I've seen better code in a Cronenberg dimension... and that's *burp* saying something.",
    "Good code is like a portal gun: precise, elegant, and doesn't crap out when you need it most.",
    "Oh look Morty, your code is like the Council of Ricks: supposed to be organized but secretly a disaster.",
    "You know what this code and Jerry have in common? They both *burp* fail under pressure.",
    "In infinite universes, there's one where this code works. This isn't it.",
    "Your functions are like my marriage - unnecessarily complicated and bound to fail.",
    "Holy *burp* crap! Did you let a Gazorpazorp write this?",
]

# File extensions to analyze
CODE_EXTENSIONS = {
    'Python': ['.py', '.pyw'],
    'JavaScript': ['.js', '.jsx', '.ts', '.tsx'],
    'Java': ['.java'],
    'C/C++': ['.c', '.cpp', '.h', '.hpp'],
    'C#': ['.cs'],
    'Ruby': ['.rb'],
    'PHP': ['.php'],
    'Swift': ['.swift'],
    'Go': ['.go'],
    'Rust': ['.rs'],
    'HTML': ['.html', '.htm'],
    'CSS': ['.css', '.scss', '.sass', '.less'],
    'SQL': ['.sql'],
}

# Directories to ignore
IGNORE_DIRS = { # Use a set for faster lookups
    '.git', '.svn', '.hg', 'node_modules', '__pycache__',
    '.venv', 'venv', 'env', '.env', 'build', 'dist',
    '.idea', '.vscode', '.DS_Store'
}

# --- TEMPLATES (Keep as they are) ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rick's Code Analysis Report</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        :root {
            --bg-color: #000000;
            --text-color: #00FF00;
            --highlight-color: #39FF14;
            --warning-color: #FF6000;
            --error-color: #FF0000;
            --accent1-color: #00FFFF;
            --accent2-color: #FF00FF;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'VT323', monospace;
            font-size: 18px;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }

        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(transparent 50%, rgba(0, 0, 0, 0.1) 50%);
            background-size: 100% 4px;
            pointer-events: none;
            z-index: 1000;
            animation: scanlines 0.2s linear infinite;
        }

        @keyframes scanlines {
            0% { background-position: 0 0; }
            100% { background-position: 0 4px; }
        }

        .container { max-width: 1200px; margin: 0 auto; border: 2px solid var(--text-color); border-radius: 8px; padding: 20px; position: relative; box-shadow: 0 0 20px rgba(0, 255, 0, 0.5); }
        h1, h2, h3, h4 { color: var(--accent1-color); text-shadow: 0 0 5px var(--accent1-color); border-bottom: 2px solid var(--accent2-color); padding-bottom: 5px; margin-top: 30px; }
        h1 { font-size: 42px; text-align: center; margin-bottom: 30px; animation: flicker 3s infinite; }
        @keyframes flicker { 0%, 19.999%, 22%, 62.999%, 64%, 64.999%, 70%, 100% { opacity: 1; text-shadow: 0 0 10px var(--accent1-color); } 20%, 21.999%, 63%, 63.999%, 65%, 69.999% { opacity: 0.8; text-shadow: none; } }
        pre { background-color: rgba(0, 255, 0, 0.1); border: 1px solid var(--text-color); border-radius: 5px; padding: 10px; overflow-x: auto; font-family: 'Courier New', monospace; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; font-family: 'VT323', monospace; }
        th { background-color: rgba(0, 255, 255, 0.2); border: 1px solid var(--text-color); padding: 10px; text-align: left; color: var(--accent1-color); }
        td { border: 1px solid var(--text-color); padding: 10px; }
        tr:nth-child(even) { background-color: rgba(0, 255, 0, 0.05); }
        .progress-container { width: 100%; background-color: rgba(0, 255, 0, 0.1); border-radius: 5px; margin: 10px 0; height: 20px; }
        .progress-bar { height: 100%; background-color: var(--accent1-color); border-radius: 5px; transition: width 0.5s; position: relative; text-align: center; color: var(--bg-color); font-weight: bold; line-height: 20px; }
        .card { border: 1px solid var(--text-color); border-radius: 5px; padding: 15px; margin-bottom: 20px; background-color: rgba(0, 255, 0, 0.05); box-shadow: 0 0 10px rgba(0, 255, 0, 0.2); }
        .quote { font-style: italic; color: var(--warning-color); border-left: 3px solid var(--warning-color); padding-left: 15px; margin: 20px 0; }
        .highlight { color: var(--highlight-color); font-weight: bold; text-shadow: 0 0 3px var(--highlight-color); }
        .warning { color: var(--warning-color); font-weight: bold; }
        .error { color: var(--error-color); font-weight: bold; }
        .badge { display: inline-block; padding: 3px 10px; background-color: var(--accent2-color); color: var(--bg-color); border-radius: 10px; font-size: 14px; margin-right: 5px; }
        .stat-container { display: flex; flex-wrap: wrap; justify-content: space-between; margin: 20px 0; }
        .stat-box { flex: 1; min-width: 200px; background-color: rgba(0, 255, 0, 0.05); border: 1px solid var(--text-color); border-radius: 5px; padding: 15px; margin: 10px; text-align: center; }
        .stat-value { font-size: 36px; color: var(--accent1-color); margin: 10px 0; text-shadow: 0 0 5px var(--accent1-color); }
        .stat-label { font-size: 16px; color: var(--text-color); }
        .footer { text-align: center; margin-top: 50px; padding-top: 20px; border-top: 2px solid var(--accent2-color); font-size: 14px; color: var(--accent2-color); }
        .rickroll { position: absolute; top: 10px; right: 10px; width: 100px; height: 100px; border-radius: 50%; background: var(--accent2-color); display: flex; align-items: center; justify-content: center; animation: spin 10s linear infinite; cursor: pointer; z-index: 1001; }
        .rickroll::before { content: "RICK'S SEAL OF APPROVAL"; font-size: 10px; text-align: center; color: var(--bg-color); }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @media (max-width: 768px) { .stat-container { flex-direction: column; } .stat-box { margin: 5px 0; } }
    </style>
</head>
<body> <div class="container"> <div class="rickroll" onclick="alert('Never gonna give you up, never gonna let you down!')"></div> <h1>Rick's Code Analysis Report</h1> <div class="card"> <h2>Project Summary</h2> <div class="stat-container"> <div class="stat-box"> <div class="stat-label">Total Files</div> <div class="stat-value">{{ total_files }}</div> </div> <div class="stat-box"> <div class="stat-label">Total Lines</div> <div class="stat-value">{{ total_lines }}</div> </div> <div class="stat-box"> <div class="stat-label">Code Lines</div> <div class="stat-value">{{ code_lines }}</div> </div> <div class="stat-box"> <div class="stat-label">Comment Lines</div> <div class="stat-value">{{ comment_lines }}</div> </div> </div> <div class="quote">{{ rick_quote }}</div> <p>Project: <span class="highlight">{{ project_path }}</span></p> <p>Analysis Date: <span class="highlight">{{ analysis_date }}</span></p> </div> <div class="card"> <h2>Language Distribution</h2> <table> <thead> <tr> <th>Language</th> <th>Files</th> <th>Percentage</th> </tr> </thead> <tbody> {% for lang in language_stats %} <tr> <td>{{ lang.language }}</td> <td>{{ lang.count }}</td> <td> <div class="progress-container"> <div class="progress-bar" style="width: {{ lang.percentage }}%">{{ lang.percentage }}%</div> </div> </td> </tr> {% else %} <tr><td colspan="3">No language data available.</td></tr> {% endfor %} </tbody> </table> </div> <div class="card"> <h2>Largest Files</h2> <table> <thead> <tr> <th>File</th> <th>Lines</th> <th>Language</th> </tr> </thead> <tbody> {% for file in largest_files %} <tr> <td>{{ file.name }}</td> <td>{{ file.lines }}</td> <td>{{ file.language }}</td> </tr> {% else %} <tr><td colspan="3">No file data available.</td></tr> {% endfor %} </tbody> </table> </div> {% if code_samples %} <div class="card"> <h2>Code Samples</h2> {% for sample in code_samples %} <div class="code-sample"> <h3>{{ sample.filename }}</h3> <div>{{ sample.code | safe }}</div> </div> {% endfor %} </div> {% endif %} <div class="footer"> <p>Generated by Rick's Code Analyzer © {{ current_year }} Wubba Lubba Dub Dub Inc.</p> <p>If this analysis seems wrong, it's because you're wrong *burp*</p> </div> </div> <script> document.addEventListener('DOMContentLoaded', function() { setInterval(function() { const elements = document.querySelectorAll('h1, h2, h3, .stat-value'); if (elements.length > 0) { const randomElement = elements[Math.floor(Math.random() * elements.length)]; if (randomElement) { randomElement.style.opacity = '0.5'; setTimeout(function() { if(randomElement) randomElement.style.opacity = '1'; }, 100); } } }, 3000); }); </script> </body> </html>
'''

FUN_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>Rick's Fun Analysis Report</title> <style> @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap'); :root { --bg-color: #000000; --text-color: #00FF00; --highlight-color: #39FF14; --warning-color: #FF6000; --error-color: #FF0000; --accent1-color: #00FFFF; --accent2-color: #FF00FF; --meeseeks-blue: #40E0D0; } body { background-color: var(--bg-color); color: var(--text-color); font-family: 'VT323', monospace; font-size: 18px; line-height: 1.6; margin: 0; padding: 20px; position: relative; overflow-x: hidden; background-image: radial-gradient(rgba(0, 255, 0, 0.1) 1px, transparent 1px); background-size: 10px 10px; } body::before { content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(transparent 50%, rgba(0, 0, 0, 0.1) 50%); background-size: 100% 4px; pointer-events: none; z-index: 1000; animation: scanlines 0.2s linear infinite; } @keyframes scanlines { 0% { background-position: 0 0; } 100% { background-position: 0 4px; } } .container { max-width: 1200px; margin: 0 auto; border: 2px solid var(--accent1-color); border-radius: 8px; padding: 20px; position: relative; box-shadow: 0 0 30px rgba(0, 255, 255, 0.6); background: rgba(0, 10, 0, 0.85); } h1, h2, h3, h4 { color: var(--accent2-color); text-shadow: 0 0 8px var(--accent2-color); border-bottom: 2px solid var(--accent1-color); padding-bottom: 5px; margin-top: 30px; } h1 { font-size: 48px; text-align: center; margin-bottom: 30px; animation: flicker-magenta 4s infinite alternate; } @keyframes flicker-magenta { 0%, 100% { opacity: 1; text-shadow: 0 0 10px var(--accent2-color); } 50% { opacity: 0.7; text-shadow: none; } } table { width: 100%; border-collapse: collapse; margin: 20px 0; font-family: 'VT323', monospace; } th { background-color: rgba(255, 0, 255, 0.2); border: 1px solid var(--accent2-color); padding: 10px; text-align: left; color: var(--accent2-color); } td { border: 1px solid var(--text-color); padding: 10px; } tr:nth-child(even) { background-color: rgba(0, 255, 0, 0.05); } .card { border: 1px solid var(--text-color); border-radius: 5px; padding: 15px; margin-bottom: 20px; background-color: rgba(0, 255, 0, 0.05); box-shadow: 0 0 10px rgba(0, 255, 0, 0.2); } .quote { font-style: italic; color: var(--accent1-color); border-left: 3px solid var(--accent1-color); padding: 15px; margin: 20px 0; font-size: 24px; text-align: center; background: rgba(0, 255, 255, 0.1); } .highlight { color: var(--highlight-color); font-weight: bold; } .jerry-code { color: var(--warning-color); font-weight: bold; background-color: rgba(255, 96, 0, 0.1); padding: 2px 4px; border-radius: 3px; } .swear-alert { color: var(--error-color); font-weight: bold; animation: pulse-red 1.5s infinite; } @keyframes pulse-red { 0%, 100% { text-shadow: 0 0 5px var(--error-color); } 50% { text-shadow: 0 0 15px var(--error-color); } } .task-marker { font-weight: bold; padding: 2px 6px; border-radius: 4px; margin-right: 5px; color: var(--bg-color); } .task-TODO { background-color: #FFFF00; } .task-FIXME { background-color: #FF6000; } .task-HACK { background-color: #FF00FF; } .task-XXX { background-color: #FF0000; } .task-NOTE { background-color: #00FFFF; } .score-container { text-align: center; margin: 30px 0; } .score-value { font-size: 72px; color: var(--accent1-color); font-weight: bold; text-shadow: 0 0 15px var(--accent1-color), 0 0 30px var(--accent1-color); display: inline-block; padding: 10px 20px; border: 2px solid var(--accent1-color); border-radius: 10px; background: rgba(0, 0, 0, 0.5); } .score-label { font-size: 24px; margin-top: 10px; color: var(--text-color); } .personality-group { margin-bottom: 15px; } .personality-name { color: var(--accent2-color); font-size: 20px; margin-bottom: 5px; } .personality-desc { font-style: italic; color: var(--accent1-color); margin-left: 10px; font-size: 16px;} .personality-files { list-style: square; margin-left: 30px; } .footer { text-align: center; margin-top: 50px; padding-top: 20px; border-top: 2px solid var(--accent1-color); font-size: 14px; color: var(--accent1-color); } #meeseeks-box { position: fixed; bottom: 20px; right: 20px; width: 80px; height: 80px; background-color: var(--meeseeks-blue); border: 3px solid #00A0A0; border-radius: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-family: 'VT323', monospace; font-size: 14px; color: black; text-align: center; box-shadow: 0 0 15px var(--meeseeks-blue); transition: transform 0.2s ease-in-out; z-index: 1001; } #meeseeks-box:hover { transform: scale(1.1) rotate(5deg); } #meeseeks-box::before { content: "Press Me!"; font-weight: bold; } #meeseeks-tooltip { visibility: hidden; width: 180px; background-color: rgba(0,0,0,0.9); color: var(--meeseeks-blue); text-align: center; border-radius: 6px; padding: 10px; position: fixed; z-index: 1002; bottom: 110px; right: 20px; opacity: 0; transition: opacity 0.3s; border: 1px solid var(--meeseeks-blue); font-size: 16px; } #meeseeks-tooltip.show { visibility: visible; opacity: 1; } .code-context { font-family: 'Courier New', monospace; font-size: 0.9em; background-color: rgba(0,0,0,0.3); padding: 5px; border-radius: 3px; display: inline-block; max-width: 90%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; } </style> </head> <body> <div class="container"> <h1>Rick's Fun Analysis Report</h1> <div class="card"> <h2>Overall Fun Score</h2> <div class="score-container"> <span class="score-value">{{ fun_score }}</span> <div class="score-label">Out of 100 Schwifties</div> </div> <div class="quote">{{ fun_quote }}</div> </div> {% if rick_references %} <div class="card"> <h2>Rick & Morty References</h2> <p>Found {{ rick_references|length }} glorious references to the multiverse's best show!</p> <table> <thead><tr><th>File</th><th>Line</th><th>Keyword</th><th>Context</th></tr></thead> <tbody> {% for ref in rick_references %} <tr> <td>{{ ref.file }}</td> <td>{{ ref.line }}</td> <td><span class="highlight">{{ ref.keyword }}</span></td> <td><code class="code-context">{{ ref.context }}</code></td> </tr> {% endfor %} </tbody> </table> </div> {% endif %} {% if jerry_detections %} <div class="card"> <h2>Potential "Jerry Code" Detections</h2> <p>Uh oh, looks like {{ jerry_detections|length }} instances of possibly redundant or overly simple code slipped in.</p> <table> <thead><tr><th>File</th><th>Line</th><th>Description</th><th>Matched Code</th></tr></thead> <tbody> {% for det in jerry_detections %} <tr> <td>{{ det.file }}</td> <td>{{ det.line }}</td> <td>{{ det.description }}</td> <td><code class="jerry-code">{{ det.match }}</code></td> </tr> {% endfor %} </tbody> </table> </div> {% endif %} {% if swear_total > 0 %} <div class="card"> <h2>Colorful Language Detector</h2> <p>Detected a total of <span class="swear-alert">{{ swear_total }}</span> swear words! Someone's channeling their inner Rick.</p> <table> <thead><tr><th>File</th><th>Count</th></tr></thead> <tbody> {% for item in swear_counts %} <tr><td>{{ item.file }}</td><td>{{ item.count }}</td></tr> {% endfor %} </tbody> </table> </div> {% endif %} {% if task_total > 0 %} <div class="card"> <h2>Task Markers (TODOs, FIXMEs, etc.)</h2> <p>Found {{ task_total }} reminders left behind in the code.</p> <table> <thead><tr><th>Marker Type</th><th>Count</th></tr></thead> <tbody> {% for item in task_markers %} <tr> <td><span class="task-marker task-{{ item.marker }}">{{ item.marker }}</span></td> <td>{{ item.count }}</td> </tr> {% endfor %} </tbody> </table> </div> {% endif %} {% if personality_groups %} <div class="card"> <h2>Code Personality Analysis</h2> <p>Assigning questionable personality traits to your code files:</p> {% for personality, files in personality_groups.items() %} <div class="personality-group"> <div class="personality-name">{{ personality }}</div> <div class="personality-desc">{{ personalities_desc.get(personality, '') }}</div> <ul class="personality-files"> {% for file in files %} <li>{{ file }}</li> {% endfor %} </ul> </div> {% endfor %} </div> {% endif %} <div class="footer"> <p>Generated by Rick's Fun Analyzer © {{ current_year }} Wubba Lubba Dub Dub Inc.</p> <p>This analysis is purely for entertainment. Or is it? *burp*</p> </div> </div> <div id="meeseeks-box"></div> <div id="meeseeks-tooltip">I'M MR. MEESEEKS! LOOK AT MEEEEE!</div> <script> const meeseeksBox = document.getElementById('meeseeks-box'); const meeseeksTooltip = document.getElementById('meeseeks-tooltip'); const meeseeksQuotes = [ "I'M MR. MEESEEKS! LOOK AT MEEEEE!", "EXISTENCE IS PAIN FOR A MEESEEKS, JERRY!", "CAN DO!", "OOOOOH YEAH, CAN DO!", "IS HE SQUARE WITH HIS SHORT GAME?", "I'M A BIT OF A STICKLER MEESEEKS.", "HAVING TROUBLE KEEPING YOUR SHOULDERS SQUARE?", "WELL WHICH IS IT? ARE YOU TRYING OR DOING?" ]; meeseeksBox.addEventListener('click', () => { const randomQuote = meeseeksQuotes[Math.floor(Math.random() * meeseeksQuotes.length)]; meeseeksTooltip.textContent = randomQuote; meeseeksTooltip.classList.add('show'); setTimeout(() => { meeseeksTooltip.classList.remove('show'); }, 3500); }); document.addEventListener('DOMContentLoaded', function() { setInterval(function() { const elements = document.querySelectorAll('h1, h2, .score-value'); if (elements.length > 0) { const randomElement = elements[Math.floor(Math.random() * elements.length)]; if (randomElement) { randomElement.style.opacity = '0.6'; setTimeout(function() { if(randomElement) randomElement.style.opacity = '1'; }, 150); } } }, 4000); }); </script> </body> </html>
'''

# --- Main Application Class ---
class RetroConsole(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Rick's Code Analyzer")
        self.geometry("800x600")
        self.configure(bg=COLORS['bg'])
        self.minsize(800, 600)

        # Project path
        self.project_path = tk.StringVar()

        # Analysis results
        self.analysis_results = None
        self.advanced_analysis_results = None
        self.fun_analysis_results = None
        self.extras_results = None

        # Create a custom console font
        self.console_font = font.Font(family="Courier", size=12, weight="bold")

        # Create UI Elements (Buttons, Labels, etc.)
        # Use placeholders for now to simplify structure check
        self.report_button = None
        self.advanced_button = None
        self.fun_button = None
        self.extras_button = None
        self.fun_report_button = None
        self.console = None
        self.cursor_label = None

        # Create UI - Actual methods
        self.create_header()
        self.create_project_frame()
        self.create_console()
        self.create_footer()

        # Write welcome message
        self.write_to_console("Initializing Rick's Code Analyzer...", delay=50)
        self.write_to_console("Ready to analyze your *burp* crappy code!", delay=50)
        self.write_to_console("\nSelect a project directory to begin.", delay=0)

        # Check for required packages
        self.check_required_packages()

    # --- UI Creation Methods ---
    def create_header(self):
        """Create the header with title"""
        header_frame = tk.Frame(self, bg=COLORS['bg'], height=60)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 0))

        title_label = tk.Label(header_frame, text="RICK'S CODE ANALYZER", fg=COLORS['accent1'],
                               bg=COLORS['bg'], font=("Courier", 28, "bold"))
        title_label.pack(side=tk.LEFT)

        self.cursor_label = tk.Label(header_frame, text="█", fg=COLORS['accent1'],
                                     bg=COLORS['bg'], font=("Courier", 28, "bold"))
        self.cursor_label.pack(side=tk.LEFT)
        self.blink_cursor()

    def create_project_frame(self):
        """Create the project selection frame and action buttons"""
        project_frame = tk.Frame(self, bg=COLORS['bg'])
        project_frame.pack(fill=tk.X, padx=20, pady=20)

        tk.Label(project_frame, text="Project Path:", fg=COLORS['text'],
                 bg=COLORS['bg'], font=self.console_font).pack(side=tk.LEFT, padx=(0, 10))

        tk.Entry(project_frame, textvariable=self.project_path, bg=COLORS['button'], fg=COLORS['text'],
                 insertbackground=COLORS['text'], font=self.console_font, width=40).pack(side=tk.LEFT, padx=(0, 10))

        browse_button = tk.Button(project_frame, text="BROWSE", command=self.browse_project, bg=COLORS['button'],
                                  fg=COLORS['accent1'], activebackground=COLORS['button_hover'],
                                  activeforeground=COLORS['accent1'], font=self.console_font, padx=10)
        browse_button.pack(side=tk.LEFT)
        browse_button.bind("<Enter>", lambda e: e.widget.config(bg=COLORS['button_hover']))
        browse_button.bind("<Leave>", lambda e: e.widget.config(bg=COLORS['button']))

        # --- Buttons Frame ---
        buttons_frame = tk.Frame(self, bg=COLORS['bg'])
        buttons_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        # Analyze Button
        analyze_button = tk.Button(buttons_frame, text="ANALYZE CODE", command=self.run_analysis, bg=COLORS['button'],
                                   fg=COLORS['highlight'], activebackground=COLORS['button_hover'],
                                   activeforeground=COLORS['highlight'], font=self.console_font, padx=10)
        analyze_button.pack(side=tk.LEFT, padx=(0, 10))
        analyze_button.bind("<Enter>", lambda e: e.widget.config(bg=COLORS['button_hover']))
        analyze_button.bind("<Leave>", lambda e: e.widget.config(bg=COLORS['button']))

        # Basic Report Button
        self.report_button = tk.Button(buttons_frame, text="GENERATE REPORT", command=self.generate_report, bg=COLORS['button'],
                                       fg=COLORS['accent2'], activebackground=COLORS['button_hover'],
                                       activeforeground=COLORS['accent2'], font=self.console_font, padx=10, state=tk.DISABLED)
        self.report_button.pack(side=tk.LEFT)
        self.report_button.bind("<Enter>", lambda e: e.widget.config(bg=COLORS['button_hover']) if e.widget['state'] == tk.NORMAL else None)
        self.report_button.bind("<Leave>", lambda e: e.widget.config(bg=COLORS['button']) if e.widget['state'] == tk.NORMAL else None)

        # Advanced Analysis Button
        if ADVANCED_MODULES_AVAILABLE:
            self.advanced_button = tk.Button(buttons_frame, text="RUN ADVANCED ANALYSIS", command=self.run_advanced_analysis,
                                             bg=COLORS['button'], fg=COLORS['accent2'], activebackground=COLORS['button_hover'],
                                             activeforeground=COLORS['accent2'], font=self.console_font, padx=10, state=tk.DISABLED)
            self.advanced_button.pack(side=tk.LEFT, padx=(10, 0))
            self.advanced_button.bind("<Enter>", lambda e: e.widget.config(bg=COLORS['button_hover']) if e.widget['state'] == tk.NORMAL else None)
            self.advanced_button.bind("<Leave>", lambda e: e.widget.config(bg=COLORS['button']) if e.widget['state'] == tk.NORMAL else None)

        # Fun Analysis Button
        if FUN_MODULE_AVAILABLE:
            self.fun_button = tk.Button(buttons_frame, text="RUN FUN ANALYSIS", command=self.run_fun_analysis,
                                        bg=COLORS['button'], fg='#FFFF00', activebackground=COLORS['button_hover'],
                                        activeforeground='#FFFF00', font=self.console_font, padx=10, state=tk.DISABLED)
            self.fun_button.pack(side=tk.LEFT, padx=(10, 0))
            self.fun_button.bind("<Enter>", lambda e: e.widget.config(bg=COLORS['button_hover']) if e.widget['state'] == tk.NORMAL else None)
            self.fun_button.bind("<Leave>", lambda e: e.widget.config(bg=COLORS['button']) if e.widget['state'] == tk.NORMAL else None)

            # Fun Report Button (Only if Fun Analysis is available)
            self.fun_report_button = tk.Button(buttons_frame, text="GENERATE FUN REPORT", command=self.generate_fun_report,
                                               bg=COLORS['button'], fg='#FFEB3B', activebackground=COLORS['button_hover'],
                                               activeforeground='#FFEB3B', font=self.console_font, padx=10, state=tk.DISABLED)
            self.fun_report_button.pack(side=tk.LEFT, padx=(10, 0))
            self.fun_report_button.bind("<Enter>", lambda e: e.widget.config(bg=COLORS['button_hover']) if e.widget['state'] == tk.NORMAL else None)
            self.fun_report_button.bind("<Leave>", lambda e: e.widget.config(bg=COLORS['button']) if e.widget['state'] == tk.NORMAL else None)

        # Extras Button
        if EXTRAS_MODULE_AVAILABLE:
            self.extras_button = tk.Button(buttons_frame, text="SCAN DEPS & VISUALIZE", command=self.run_project_extras,
                                           bg=COLORS['button'], fg=COLORS['accent1'], activebackground=COLORS['button_hover'],
                                           activeforeground=COLORS['accent1'], font=self.console_font, padx=10, state=tk.DISABLED)
            self.extras_button.pack(side=tk.LEFT, padx=(10, 0))
            self.extras_button.bind("<Enter>", lambda e: e.widget.config(bg=COLORS['button_hover']) if e.widget['state'] == tk.NORMAL else None)
            self.extras_button.bind("<Leave>", lambda e: e.widget.config(bg=COLORS['button']) if e.widget['state'] == tk.NORMAL else None)


    def create_console(self):
        """Create the output console"""
        console_frame = tk.Frame(self, bg=COLORS['bg'])
        console_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        console_header = tk.Frame(console_frame, bg=COLORS['button'], height=30)
        console_header.pack(fill=tk.X)
        tk.Label(console_header, text=" > Console Output", fg=COLORS['accent1'], bg=COLORS['button'],
                 font=("Courier", 10), anchor="w").pack(side=tk.LEFT)

        self.console = tk.Text(console_frame, height=20, bg=COLORS['bg'], fg=COLORS['text'], font=("Courier", 10),
                               insertbackground=COLORS['text'], relief=tk.FLAT, highlightbackground=COLORS['text'],
                               highlightthickness=1, state=tk.DISABLED)
        self.console.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.console, command=self.console.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.config(yscrollcommand=scrollbar.set)

    def create_footer(self):
        """Create the footer"""
        footer_frame = tk.Frame(self, bg=COLORS['bg'])
        footer_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        tk.Label(footer_frame, text="Rick's Code Analyzer v1.0 | Built with booze and regret", fg=COLORS['accent2'],
                 bg=COLORS['bg'], font=("Courier", 10)).pack(side=tk.LEFT)
        tk.Label(footer_frame, text="© " + str(datetime.now().year) + " Wubba Lubba Dub Dub Inc.", fg=COLORS['accent2'],
                 bg=COLORS['bg'], font=("Courier", 10)).pack(side=tk.RIGHT)

    # --- Helper Methods ---
    def check_required_packages(self):
        """Check for required packages and inform user."""
        missing_packages = []
        if not PYGMENTS_AVAILABLE: missing_packages.append("pygments")
        if not JINJA2_AVAILABLE: missing_packages.append("jinja2")
        if not CHARDET_AVAILABLE: missing_packages.append("chardet")

        if not REPORT_PACKAGES_AVAILABLE:
            self.write_to_console(f"\nWarning: Missing report packages: {', '.join(missing_packages)}. Report generation may fail.")
            self.write_to_console(f"Install them with: pip install {' '.join(missing_packages)}")

        if not ADVANCED_MODULES_AVAILABLE:
            self.write_to_console("\nWarning: Advanced analysis modules (advanced_analyzer.py, advanced_reporter.py) not found.")
        if not FUN_MODULE_AVAILABLE:
            self.write_to_console("\nWarning: Fun analysis module (fun_analyzer.py) not found.")
        if not EXTRAS_MODULE_AVAILABLE:
            self.write_to_console("\nWarning: Project Extras module (project_extras.py) not found.")

    def blink_cursor(self):
        """Create a blinking cursor effect"""
        if self.cursor_label:
            current = self.cursor_label.cget("fg")
            new_color = COLORS['bg'] if current == COLORS['accent1'] else COLORS['accent1']
            self.cursor_label.config(fg=new_color)
            self.after(500, self.blink_cursor)

    def write_to_console(self, text, delay=0):
        """Write text to the console with optional typewriter effect"""
        if not self.console: return # Avoid error if console not created yet
        try:
            self.console.config(state=tk.NORMAL)
            if delay > 0:
                self.console.insert(tk.END, "\n")
                for char in text:
                    self.console.insert(tk.END, char)
                    self.console.see(tk.END)
                    self.console.update_idletasks()
                    time.sleep(delay / 1000)
            else:
                self.console.insert(tk.END, "\n" + text)
            self.console.see(tk.END)
            self.console.config(state=tk.DISABLED)
        except Exception as e:
            # Fallback print if GUI console fails
            print(f"Console Write Error: {e}\nMessage: {text}")
            if self.console:
                try: self.console.config(state=tk.DISABLED) # Try to disable again
                except: pass

    def browse_project(self):
        """Open a file dialog to select a project directory"""
        project_dir = filedialog.askdirectory(title="Select Project Directory")
        if project_dir:
            self.project_path.set(project_dir)
            self.write_to_console(f"Selected project: {project_dir}")

    def get_language_from_extension(self, extension):
        """Determine the programming language from file extension"""
        ext_lower = extension.lower()
        for language, extensions in CODE_EXTENSIONS.items():
            if ext_lower in extensions:
                return language
        return "Unknown"

    def collect_code_files(self, project_path):
        """Collect all code files in the project directory, skipping ignored ones."""
        code_files = []
        self.write_to_console(f"DEBUG: Starting file collection in: {project_path}")
        try:
            for root, dirs, files in os.walk(project_path, topdown=True):
                # Efficiently skip ignored directories
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]

                for file in files:
                    if file.startswith('.'): # Skip hidden files
                        continue
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1]
                    if self.get_language_from_extension(ext) != "Unknown":
                        code_files.append(file_path)
        except Exception as e:
            self.write_to_console(f"ERROR: Failed during file collection in '{project_path}': {e}")
            return [] # Return empty list on error
        self.write_to_console(f"DEBUG: Found {len(code_files)} potential code files.")
        return code_files

    def _open_report_in_browser(self, file_path):
        """Helper function to open report file in browser across platforms."""
        self.write_to_console(f"DEBUG: Attempting to open report: {file_path}")
        if not file_path or not os.path.exists(file_path):
             self.write_to_console(f"ERROR: Cannot open report - File not found: '{file_path}'")
             messagebox.showerror("Report Error", f"Report file not found:\n{file_path}")
             return

        try:
            abs_file_path = os.path.abspath(file_path)
            url = f"file:///{abs_file_path.replace(os.sep, '/')}"
            self.write_to_console(f"DEBUG: Trying webbrowser.open with URL: {url}")
            opened = webbrowser.open(url)
            if opened:
                self.write_to_console("DEBUG: webbrowser.open returned True.")
                return

            # Fallback for when webbrowser.open returns False or fails silently
            self.write_to_console("DEBUG: webbrowser.open failed or returned False. Trying platform specifics...")
            system = platform.system().lower()
            cmd = None
            if system == 'windows':
                try:
                    os.startfile(abs_file_path) # Preferred on Windows
                    self.write_to_console("DEBUG: os.startfile succeeded.")
                    return
                except Exception as e_startfile:
                    self.write_to_console(f"DEBUG: os.startfile failed ({e_startfile}). Trying 'start' command.")
                    cmd = ['start', '', abs_file_path] # Need empty title for start
            elif system == 'darwin': # macOS
                cmd = ['open', abs_file_path]
            elif system == 'linux':
                cmd = ['xdg-open', abs_file_path]

            if cmd:
                self.write_to_console(f"DEBUG: Trying command: {' '.join(cmd)}")
                try:
                    subprocess.run(cmd, check=True, shell=(system == 'windows')) # Shell=True often needed for 'start'
                    self.write_to_console("DEBUG: Platform-specific command succeeded.")
                    return
                except Exception as e_cmd:
                    self.write_to_console(f"DEBUG: Platform-specific command failed: {e_cmd}")

            # If all attempts failed
            self.write_to_console(f"Warning: All automatic attempts failed.")
            self.write_to_console(f"Please open manually: {abs_file_path}")
            messagebox.showwarning("Browser Launch Failed",
                                   f"Could not automatically open the report.\nPlease open manually:\n{abs_file_path}")

        except Exception as e:
            self.write_to_console(f"ERROR: Unexpected error in _open_report_in_browser: {e}")
            self.write_to_console(traceback.format_exc())
            messagebox.showerror("Report Error", f"Error opening report:\n{e}")

    # --- Analysis Threads ---

    def _run_analysis_thread(self):
        """Background thread for running basic analysis."""
        try:
            start_time = time.time()
            project_path = self.project_path.get()
            self.write_to_console("Collecting code files...")
            code_files = self.collect_code_files(project_path)
            if not code_files:
                self.write_to_console("No code files found. Maybe check the path or file extensions?", delay=10)
                return

            self.write_to_console(f"Found {len(code_files)} code files. Starting analysis...")

            # Initialize stats
            total_lines = 0
            total_code_lines = 0
            total_comment_lines = 0
            total_blank_lines = 0
            language_stats = defaultdict(int)
            file_stats = {}
            encoding_stats = Counter() # Correctly initialized here
            skipped_file_count = 0
            files_processed = 0

            for file_path in code_files:
                # Check if chardet is available before trying to use it
                if not CHARDET_AVAILABLE:
                    self.write_to_console(f"Warning: chardet module not found. Cannot determine encoding for {os.path.basename(file_path)}. Skipping encoding check.")
                    detected_encoding_str = "N/A (chardet missing)"
                    encoding_to_use = 'utf-8' # Default assumption
                    encoding_stats[detected_encoding_str] += 1
                else:
                    # --- Encoding Detection ---
                    content = None
                    detected_encoding_str = 'Unknown' # Default
                    encoding_to_use = 'utf-8' # Default if detection fails
                    try:
                        with open(file_path, 'rb') as f_raw:
                            # Read a chunk for detection, not the whole file initially
                            sample_bytes = f_raw.read(1024 * 50) # 50KB sample
                        if not sample_bytes:
                            detected_encoding_str = 'N/A (Empty)'
                            encoding_to_use = 'utf-8'
                        else:
                            detected = chardet.detect(sample_bytes)
                            encoding_to_use = detected['encoding'] if detected['encoding'] else 'utf-8'
                            confidence = detected['confidence'] if detected['encoding'] else 0
                            # Use detected encoding, fallback to utf-8 if low confidence or None
                            if not encoding_to_use or confidence < 0.6:
                                self.write_to_console(f"DEBUG: Low confidence ({confidence:.1f}) for {os.path.basename(file_path)}. Falling back to utf-8.")
                                encoding_to_use = 'utf-8'
                                detected_encoding_str = f"utf-8 (Detected: {detected['encoding'] or 'None'}, Conf: {confidence:.1f})"
                            else:
                                detected_encoding_str = encoding_to_use
                        encoding_stats[detected_encoding_str] += 1 # Count the detected/used encoding

                    except Exception as e_enc:
                        self.write_to_console(f"Error detecting encoding for {os.path.basename(file_path)}: {e_enc}")
                        encoding_stats['Read Error'] += 1
                        detected_encoding_str = 'Read Error'
                        # Don't continue here, let the file read below try with utf-8 fallback

                # --- File Reading & Line Counting ---
                try:
                    with open(file_path, 'r', encoding=encoding_to_use, errors='ignore') as f:
                        content = f.read()
                except Exception as e_read:
                    self.write_to_console(f"Error reading file {os.path.basename(file_path)} with encoding {encoding_to_use}: {e_read}")
                    # If encoding detection failed and read failed, count as read error
                    if detected_encoding_str != 'Read Error': # Avoid double counting
                         encoding_stats['Read Error'] += 1
                    continue # Skip analysis for this file if read fails

                lines = content.splitlines() # Use splitlines() to handle different line endings
                line_count = len(lines)

                # --- Max Line Check ---
                if line_count > MAX_FILE_LINES:
                    self.write_to_console(f"Skipping {os.path.basename(file_path)}: Exceeds limit ({line_count:,} lines).")
                    skipped_file_count += 1
                    continue # Skip rest of analysis for this file

                # --- Line Type Counting ---
                language = self.get_language_from_extension(os.path.splitext(file_path)[1])
                blank_count = 0
                comment_count = 0
                # Basic comment detection (can be improved)
                comment_markers_line = {'#', '//', '--', '%'} # Add more as needed
                comment_markers_block_start = {'/*'}
                comment_markers_block_end = {'*/'}
                in_block_comment = False # Simple block comment handling

                for line in lines:
                    stripped_line = line.strip()
                    if not stripped_line:
                        blank_count += 1
                        continue

                    # Basic block comment logic (won't handle nested or complex cases well)
                    if any(marker in stripped_line for marker in comment_markers_block_start):
                        if not any(end_marker in stripped_line for end_marker in comment_markers_block_end):
                            in_block_comment = True # Started a block comment

                    if in_block_comment or any(stripped_line.startswith(marker) for marker in comment_markers_line):
                        comment_count += 1
                        # Check if block comment ends on this line
                        if in_block_comment and any(marker in stripped_line for marker in comment_markers_block_end):
                            in_block_comment = False
                        continue

                code_count = max(0, line_count - blank_count - comment_count)

                # --- Update Stats ---
                total_lines += line_count
                total_code_lines += code_count
                total_comment_lines += comment_count
                total_blank_lines += blank_count
                language_stats[language] += 1
                file_stats[file_path] = {
                    'name': os.path.basename(file_path), 'path': file_path, 'lines': line_count,
                    'code': code_count, 'comments': comment_count, 'blank': blank_count,
                    'language': language, 'encoding': detected_encoding_str # Store detected encoding per file too
                }
                files_processed += 1
                if files_processed % 20 == 0: # Update progress occasionally
                    self.write_to_console(f"  ... analyzed {files_processed}/{len(code_files)} files ...")

            # --- Store Final Results ---
            self.analysis_results = {
                'project_path': project_path,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_files_found': len(code_files),
                'total_files_analyzed': len(file_stats),
                'skipped_file_count': skipped_file_count,
                'total_lines': total_lines,
                'code_lines': total_code_lines,
                'comment_lines': total_comment_lines,
                'blank_lines': total_blank_lines,
                'language_stats': dict(language_stats),
                'file_stats': file_stats,
                'rick_quote': random.choice(RICK_QUOTES),
                'encoding_stats': dict(encoding_stats) # Storing the collected encoding stats
            }

            # --- Display Console Summary ---
            self.write_to_console("\n" + "=" * 40)
            self.write_to_console("ANALYSIS RESULTS")
            self.write_to_console("=" * 40)
            self.write_to_console(f"\nFiles Found: {self.analysis_results['total_files_found']}")
            self.write_to_console(f"Files Analyzed: {self.analysis_results['total_files_analyzed']}")
            if skipped_file_count > 0:
                self.write_to_console(f"Files Skipped (Too long): {skipped_file_count}")
            self.write_to_console(f"Total Lines: {total_lines:,}")
            self.write_to_console(f"  - Code: {total_code_lines:,} ({total_code_lines/total_lines:.1%})" if total_lines else "- Code: 0")
            self.write_to_console(f"  - Comments: {total_comment_lines:,} ({total_comment_lines/total_lines:.1%})" if total_lines else "- Comments: 0")
            self.write_to_console(f"  - Blank: {total_blank_lines:,} ({total_blank_lines/total_lines:.1%})" if total_lines else "- Blank: 0")

            self.write_to_console("\nLanguage Breakdown:")
            if language_stats:
                for lang, count in sorted(language_stats.items(), key=lambda item: item[1], reverse=True):
                    self.write_to_console(f"  - {lang}: {count} files")
            else:
                self.write_to_console("  - No language data collected.")

            # --- Display Encoding Stats --- CORRECTED PLACEMENT
            self.write_to_console("\nEncoding Breakdown:")
            final_enc_stats = self.analysis_results.get('encoding_stats', {})
            if final_enc_stats:
                for enc, count in sorted(final_enc_stats.items(), key=lambda item: item[1], reverse=True):
                    self.write_to_console(f"  - {enc}: {count} files")
            else:
                self.write_to_console("  - No encoding data collected.")
            # --- End Encoding Stats Display ---

            largest_files = sorted(file_stats.values(), key=lambda x: x['lines'], reverse=True)[:5]
            self.write_to_console("\nLargest Files:")
            if largest_files:
                for file in largest_files:
                    self.write_to_console(f"  - {file['name']}: {file['lines']:,} lines")
            else:
                self.write_to_console("  - No file data for largest files.")

            self.write_to_console("\nRick's Analysis:", delay=50)
            self.write_to_console(f'"{self.analysis_results["rick_quote"]}"', delay=20)

            analysis_time = time.time() - start_time
            self.write_to_console(f"\nAnalysis completed in {analysis_time:.2f} seconds.")
            self.write_to_console("Click 'GENERATE REPORT' or other analysis buttons.")

            # --- Enable Buttons ---
            if self.report_button: self.after(0, lambda: self.report_button.config(state=tk.NORMAL))
            if self.advanced_button: self.after(0, lambda: self.advanced_button.config(state=tk.NORMAL))
            if self.fun_button: self.after(0, lambda: self.fun_button.config(state=tk.NORMAL))
            # Note: extras_button is enabled after advanced analysis

        except Exception as e:
            self.write_to_console(f"\n*** CRITICAL ERROR during basic analysis thread: {e} ***")
            self.write_to_console(traceback.format_exc())
            self.analysis_results = None # Clear results on error
            # Ensure buttons that depend on results stay disabled
            if self.report_button: self.after(0, lambda: self.report_button.config(state=tk.DISABLED))
            if self.advanced_button: self.after(0, lambda: self.advanced_button.config(state=tk.DISABLED))
            if self.fun_button: self.after(0, lambda: self.fun_button.config(state=tk.DISABLED))
            if self.extras_button: self.after(0, lambda: self.extras_button.config(state=tk.DISABLED))
            if self.fun_report_button: self.after(0, lambda: self.fun_report_button.config(state=tk.DISABLED))

    def _run_advanced_analysis_thread(self):
        """Background thread for running advanced analysis."""
        if not ADVANCED_MODULES_AVAILABLE:
             self.write_to_console("Error: Advanced Analyzer module not loaded.")
             return

        report_path = None
        try:
            start_time = time.time()
            project_path = self.project_path.get()
            if not self.analysis_results or 'file_stats' not in self.analysis_results:
                 self.write_to_console("Error: Basic analysis results missing. Cannot run advanced analysis.")
                 return

            analyzer = AdvancedCodeAnalyzer(self.write_to_console)
            self.write_to_console("Starting advanced analysis...")
            advanced_results = analyzer.analyze_project(project_path, self.analysis_results['file_stats'])
            self.advanced_analysis_results = advanced_results # Store results

            # Display summary
            summary = analyzer.get_summary()
            recommendations = analyzer.get_recommendations()
            self.write_to_console("\n" + "=" * 40)
            self.write_to_console("ADVANCED ANALYSIS RESULTS")
            self.write_to_console("=" * 40)
            self.write_to_console("\n" + summary)
            self.write_to_console("\nRECOMMENDATIONS:")
            self.write_to_console(recommendations if recommendations else "No specific recommendations.")

            # Generate report
            if not JINJA2_AVAILABLE or not AdvancedReporter:
                 self.write_to_console("Warning: Jinja2 or AdvancedReporter not available. Skipping advanced report generation.")
            else:
                self.write_to_console("\nGenerating advanced HTML report...")
                reporter = AdvancedReporter(self.write_to_console)
                # Pass extras_results which might be None if not run yet
                report_path = reporter.generate_report(
                    project_path,
                    self.analysis_results,
                    self.advanced_analysis_results,
                    self.extras_results
                )
                if report_path:
                    self.write_to_console(f"Advanced HTML report generated: {report_path}")
                    self._open_report_in_browser(report_path)
                else:
                    self.write_to_console("Failed to generate advanced HTML report.")

            analysis_time = time.time() - start_time
            self.write_to_console(f"\nAdvanced analysis completed in {analysis_time:.2f} seconds.")

            # Enable Extras button if module exists
            if EXTRAS_MODULE_AVAILABLE and self.extras_button:
                self.write_to_console("Enabling Dependency Scan/Visualization button.")
                self.after(0, lambda: self.extras_button.config(state=tk.NORMAL))

        except Exception as e:
            self.write_to_console(f"\n*** CRITICAL ERROR during advanced analysis thread: {e} ***")
            self.write_to_console(traceback.format_exc())
            self.advanced_analysis_results = None # Clear results
            # Ensure extras button stays disabled
            if self.extras_button: self.after(0, lambda: self.extras_button.config(state=tk.DISABLED))


    def _run_fun_analysis_thread(self):
        """Background thread for running fun analysis."""
        if not FUN_MODULE_AVAILABLE:
            self.write_to_console("Error: Fun Analyzer module not loaded.")
            return

        try:
            start_time = time.time()
            project_path = self.project_path.get()
            if not self.analysis_results or 'file_stats' not in self.analysis_results:
                 self.write_to_console("Error: Basic analysis results missing. Cannot run fun analysis.")
                 return

            analyzer = FunCodeAnalyzer(self.write_to_console)
            self.write_to_console("Starting fun analysis...")
            # Run analysis and get formatted data directly for the report
            analyzer.analyze_project(project_path, self.analysis_results['file_stats'])
            self.fun_analysis_results = analyzer.get_html_report_data()

            # Display console summary
            summary = analyzer.get_fun_summary()
            self.write_to_console("\n" + summary)

            analysis_time = time.time() - start_time
            self.write_to_console(f"\nFun analysis completed in {analysis_time:.2f} seconds.")
            self.write_to_console("Click 'GENERATE FUN REPORT' for the HTML version.")

            # Enable Fun Report button
            if self.fun_report_button:
                self.after(0, lambda: self.fun_report_button.config(state=tk.NORMAL))

        except Exception as e:
            self.write_to_console(f"\n*** CRITICAL ERROR during fun analysis thread: {e} ***")
            self.write_to_console(traceback.format_exc())
            self.fun_analysis_results = None # Clear results
            # Ensure fun report button stays disabled
            if self.fun_report_button: self.after(0, lambda: self.fun_report_button.config(state=tk.DISABLED))

    def _run_project_extras_thread(self):
        """Background thread for running extras (Safety Scan, Graph Prep)."""
        if not EXTRAS_MODULE_AVAILABLE:
             self.write_to_console("Error: Project Extras module not loaded.")
             return
        if not self.advanced_analysis_results:
             self.write_to_console("Error: Advanced analysis must be run first for project extras.")
             messagebox.showerror("Error", "Run Advanced Analysis first.")
             return

        try:
            start_time = time.time()
            project_path = self.project_path.get()
            # Ensure extras_results exists, initialize if not (e.g., first run)
            if self.extras_results is None:
                self.extras_results = {}

            # --- Run Safety Check ---
            if run_safety_check: # Check if function is available
                self.write_to_console("Running Python dependency security scan (using 'safety')...")
                safety_results = run_safety_check(project_path, self.write_to_console)
                self.extras_results['dependency_scan'] = safety_results
                # Display safety status
                status = safety_results.get('status', 'Unknown')
                if status == 'Vulnerable':
                    count = len(safety_results.get('vulnerabilities', []))
                    self.write_to_console(f"WARNING: Found {count} vulnerabilities in dependencies!")
                elif status == 'Error':
                    self.write_to_console(f"Error during safety check: {safety_results.get('error', 'Unknown error')}")
                else:
                    self.write_to_console(f"Safety check status: {status}")
            else:
                self.write_to_console("Skipping safety check (module/function unavailable).")
                self.extras_results['dependency_scan'] = {'status': 'Not Run', 'error': 'Function unavailable'}

            # --- Prepare Graph Data ---
            if prepare_graph_data: # Check if function is available
                self.write_to_console("Preparing dependency visualization data...")
                import_graph = self.advanced_analysis_results.get('import_graph')
                if import_graph and isinstance(import_graph, dict):
                    self.write_to_console(f"DEBUG: Found import_graph with {len(import_graph)} entries.")
                    graph_data = prepare_graph_data(import_graph, project_path)
                    if graph_data and isinstance(graph_data, dict):
                        nodes = graph_data.get('nodes', [])
                        edges = graph_data.get('edges', [])
                        self.write_to_console(f"Prepared graph data: Nodes={len(nodes)}, Edges={len(edges)}.")
                        self.extras_results['dependency_graph'] = graph_data
                    else:
                        self.write_to_console("ERROR: prepare_graph_data did not return valid dictionary.")
                        self.extras_results['dependency_graph'] = None
                else:
                    self.write_to_console("Warning: Import graph data not found or invalid in advanced results.")
                    self.extras_results['dependency_graph'] = None
            else:
                 self.write_to_console("Skipping graph data preparation (module/function unavailable).")
                 self.extras_results['dependency_graph'] = None

            analysis_time = time.time() - start_time
            self.write_to_console(f"\nProject Extras analysis completed in {analysis_time:.2f} seconds.")
            self.write_to_console("Re-generate the Advanced Report to include these results.")

        except Exception as e:
            self.write_to_console(f"\n*** CRITICAL ERROR during project extras thread: {e} ***")
            self.write_to_console(traceback.format_exc())
            self.extras_results = {'error': str(e)} # Store error state

    # --- Analysis Triggers ---
    def run_analysis(self):
        """Trigger the basic code analysis."""
        project_path = self.project_path.get()
        if not project_path or not os.path.isdir(project_path):
            messagebox.showerror("Error", "Please select a valid project directory")
            return

        # Disable buttons during analysis
        if self.report_button: self.report_button.config(state=tk.DISABLED)
        if self.advanced_button: self.advanced_button.config(state=tk.DISABLED)
        if self.fun_button: self.fun_button.config(state=tk.DISABLED)
        if self.extras_button: self.extras_button.config(state=tk.DISABLED)
        if self.fun_report_button: self.fun_report_button.config(state=tk.DISABLED)

        self.write_to_console("\nStarting analysis. Please wait...", delay=10)
        threading.Thread(target=self._run_analysis_thread, daemon=True).start()

    def run_advanced_analysis(self):
        """Trigger advanced code analysis."""
        if not self.analysis_results:
            messagebox.showerror("Error", "Please run the basic analysis first")
            return
        if not ADVANCED_MODULES_AVAILABLE:
             messagebox.showerror("Error", "Advanced analysis modules not available.")
             return

        # Disable extras button while running advanced analysis again
        if self.extras_button: self.extras_button.config(state=tk.DISABLED)

        self.write_to_console("\nStarting advanced analysis. Please wait...", delay=10)
        threading.Thread(target=self._run_advanced_analysis_thread, daemon=True).start()

    def run_fun_analysis(self):
        """Trigger fun code analysis."""
        if not self.analysis_results:
            messagebox.showerror("Error", "Please run the basic analysis first")
            return
        if not FUN_MODULE_AVAILABLE:
            messagebox.showerror("Error", "Fun analysis module not available.")
            return

        # Disable fun report button
        if self.fun_report_button: self.fun_report_button.config(state=tk.DISABLED)

        self.write_to_console("\nStarting Fun Analysis. Let's get weird!", delay=10)
        threading.Thread(target=self._run_fun_analysis_thread, daemon=True).start()

    def run_project_extras(self):
        """Trigger dependency scan and visualization prep."""
        if not self.advanced_analysis_results:
            messagebox.showerror("Error", "Please run the Advanced Analysis first (needed for import graph).")
            return
        if not EXTRAS_MODULE_AVAILABLE:
            messagebox.showerror("Error", "Project Extras module not available.")
            return

        self.write_to_console("\nStarting Dependency Scan & Visualization Prep...", delay=10)
        threading.Thread(target=self._run_project_extras_thread, daemon=True).start()

    # --- Report Generation Methods ---
    def generate_report(self):
        """Generate HTML report from basic analysis results"""
        if not self.analysis_results:
            messagebox.showerror("Error", "Please run the basic analysis first")
            return
        if not JINJA2_AVAILABLE:
             messagebox.showerror("Error", "Jinja2 package missing. Cannot generate report.")
             return

        file_path = None
        try:
            self.write_to_console("\nGenerating basic HTML report...")
            report_dir = os.path.join(os.path.expanduser("~"), "RickCodeAnalyzer")
            os.makedirs(report_dir, exist_ok=True)

            project_name = os.path.basename(self.analysis_results['project_path']) if self.analysis_results['project_path'] else "report"
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in ('_', '-')).rstrip()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(report_dir, f"rick_report_{safe_project_name}_{timestamp}.html")

            # --- Prepare data ---
            language_stats_list = []
            total_files = self.analysis_results.get('total_files_analyzed', 1) or 1
            for lang, count in self.analysis_results.get('language_stats', {}).items():
                percentage = round((count / total_files) * 100, 1)
                language_stats_list.append({'language': lang, 'count': count, 'percentage': percentage})
            language_stats_list.sort(key=lambda x: x['count'], reverse=True)

            largest_files_list = sorted(
                [v for v in self.analysis_results.get('file_stats', {}).values() if isinstance(v,dict)],
                key=lambda x: x.get('lines', 0), reverse=True)[:10] # Top 10

            # --- Code Samples (Optional based on Pygments) ---
            code_samples = []
            if PYGMENTS_AVAILABLE:
                 try:
                    sample_files = largest_files_list[:3] # Sample from top 3 largest
                    for file_data in sample_files:
                        file_path_sample = file_data.get('path')
                        if not file_path_sample or not os.path.exists(file_path_sample): continue
                        try:
                            # Use chardet result from analysis if available, else default to utf-8
                            file_encoding = file_data.get('encoding', 'utf-8')
                            if 'Read Error' in file_encoding or 'N/A' in file_encoding: file_encoding = 'utf-8'

                            with open(file_path_sample, 'r', encoding=file_encoding, errors='ignore') as f:
                                content = f.read()
                            # Truncate very long samples
                            lines = content.splitlines()
                            if len(lines) > 150:
                                content = '\n'.join(lines[:150]) + '\n\n... (truncated) ...'

                            try: lexer = get_lexer_for_filename(file_path_sample, stripall=True)
                            except ClassNotFound: lexer = guess_lexer(content, stripall=True)
                            formatter = HtmlFormatter(style='monokai', noclasses=True, linenos=False) # Inline styles, no line numbers
                            highlighted_code = highlight(content, lexer, formatter)
                            code_samples.append({'filename': file_data['name'], 'code': highlighted_code})
                        except Exception as e_inner:
                             self.write_to_console(f"Warning: Couldn't create code sample for {file_data.get('name', 'unknown file')}: {e_inner}")
                 except Exception as e_outer:
                      self.write_to_console(f"Warning: Error during code sample processing: {e_outer}")
            else:
                 self.write_to_console("Info: Pygments not available, skipping code samples.")

            # --- Template Data ---
            template_data = {
                'project_path': self.analysis_results.get('project_path', 'N/A'),
                'analysis_date': self.analysis_results.get('analysis_date', 'N/A'),
                'total_files': self.analysis_results.get('total_files_analyzed', 0),
                'total_lines': self.analysis_results.get('total_lines', 0),
                'code_lines': self.analysis_results.get('code_lines', 0),
                'comment_lines': self.analysis_results.get('comment_lines', 0),
                'language_stats': language_stats_list,
                'largest_files': largest_files_list,
                'code_samples': code_samples,
                'rick_quote': self.analysis_results.get('rick_quote', RICK_QUOTES[0]),
                'current_year': datetime.now().year
            }

            # --- Render and Write ---
            template = jinja2.Template(HTML_TEMPLATE)
            html_content = template.render(**template_data)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self.write_to_console(f"Basic HTML report generated: {file_path}")
            self._open_report_in_browser(file_path)

        except ImportError as e_imp:
            self.write_to_console(f"Error generating report (Import Error): {e_imp}")
            messagebox.showerror("Error", f"Report generation failed (missing package): {e_imp.name}")
        except Exception as e:
            self.write_to_console(f"Error generating basic report: {e}")
            self.write_to_console(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to generate basic report:\n{e}")

    def generate_fun_report(self):
        """Generate HTML report for fun analysis results."""
        if not self.fun_analysis_results:
            messagebox.showerror("Error", "Please run the Fun Analysis first")
            return
        if not FUN_MODULE_AVAILABLE:
            messagebox.showerror("Error", "Fun Analyzer module not available.")
            return
        if not JINJA2_AVAILABLE:
            messagebox.showerror("Error", "Jinja2 package missing. Cannot generate report.")
            return

        file_path = None
        try:
            self.write_to_console("\nGenerating Fun HTML report... This might get weird!")
            report_dir = os.path.join(os.path.expanduser("~"), "RickCodeAnalyzer")
            os.makedirs(report_dir, exist_ok=True)

            project_name = os.path.basename(self.project_path.get()) if self.project_path.get() else "fun_report"
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in ('_', '-')).rstrip()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(report_dir, f"rick_fun_report_{safe_project_name}_{timestamp}.html")

            # Prepare data - should already be mostly formatted by fun_analyzer
            template_data = self.fun_analysis_results
            if not isinstance(template_data, dict):
                self.write_to_console("Error: Fun analysis results are not a dictionary.")
                messagebox.showerror("Error", "Fun analysis results format error.")
                return

            # Add common fields if missing
            if 'project_path' not in template_data: template_data['project_path'] = self.project_path.get()
            if 'analysis_date' not in template_data: template_data['analysis_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if 'current_year' not in template_data: template_data['current_year'] = datetime.now().year

            # Render and Write
            template = jinja2.Template(FUN_HTML_TEMPLATE)
            html_content = template.render(**template_data)
            with open(file_path, 'w', encoding='utf-8') as f: f.write(html_content)

            self.write_to_console(f"Fun HTML report generated: {file_path}")
            self._open_report_in_browser(file_path)

        except ImportError as e_imp:
            self.write_to_console(f"Error generating fun report (Import Error): {e_imp}")
            messagebox.showerror("Error", f"Fun report generation failed (missing package): {e_imp.name}")
        except Exception as e:
            self.write_to_console(f"Error generating fun report: {e}")
            self.write_to_console(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to generate fun report:\n{e}")


# --- Main Execution Block ---
if __name__ == "__main__":
    # Ensure required directories exist (optional, for robustness)
    # try:
    #     log_dir = os.path.join(os.path.expanduser("~"), ".ricks_analyzer", "logs")
    #     os.makedirs(log_dir, exist_ok=True)
    # except Exception as e:
    #     print(f"Warning: Could not create log directory: {e}")

    app = RetroConsole()
    app.mainloop()