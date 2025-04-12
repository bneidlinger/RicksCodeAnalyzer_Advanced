#!/usr/bin/env python3
# Advanced Reporter Module for Rick's Code Analyzer
# v4.3 - Fixed f-string syntax error for {} in generated JS

import os
import json
import random
import datetime
import webbrowser
import tempfile
from collections import defaultdict, Counter
import traceback

# --- Required Package Checks ---
REPORT_PACKAGES_AVAILABLE = True
PYGMENTS_AVAILABLE = True

try:
    import jinja2
except ImportError:
    REPORT_PACKAGES_AVAILABLE = False

try:
    from pygments import highlight, lexers, formatters, util
except ImportError:
    PYGMENTS_AVAILABLE = False

# --- Global Data Definitions ---
# (Keep the RICK_QUOTES and QUALITY_RATINGS dictionaries defined here as before)
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

QUALITY_RATINGS = {
    'excellent': [
        "This code is *burp* beautiful! Like gazing into an abyss of pure logic.",
        "Schwifty! This code gets an A+ in my dimension.",
        "It's perfect... almost *too* perfect. Makes me suspicious."
    ],
    'good': [
        "Alright, Morty, not bad. You didn't completely screw *burp* it up.",
        "Looks like you actually put some thought into this. Passable.",
        "This is... acceptable. Now get me a portal gun cleaner."
    ],
    'fair': [
        "Meh, it'll do. Like a Plumbus, it functions... mostly.",
        "It's not great, not terrible. The 'Jerry' of code quality.",
        "Could be worse. Could be infested with *burp* Gazorpazorps."
    ],
    'poor': [
        "Seriously? Did Jerry write this part? It's got his stink all over it.",
        "This is the kind of code that leads to Cronenberg monsters, Morty!",
        "My disappointment is immeasurable, and my day is *burp* ruined."
    ],
    'very_poor': [
        "Wubba lubba dub dub! This code's a *burp* disaster!",
        "This isn't code, it's a cry for help wrapped in syntax errors.",
        "Abort mission! This whole section needs to be *burp* purged!"
    ]
}


# --- HTML TEMPLATE (Unchanged from v4.2) ---
HTML_REPORT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rick's Advanced Code Analysis Report</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        /* Keep ALL existing CSS rules */
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
        :root { --bg-color: #000000; --text-color: #00FF00; --highlight-color: #39FF14; --warning-color: #FF6000; --error-color: #FF0000; --critical-color: #FF00FF; --accent1-color: #00FFFF; --accent2-color: #FF00FF; --code-bg: rgba(0, 30, 0, 0.5); --card-bg: rgba(0, 20, 0, 0.8); } /* Added some missing vars for context */
        body { background-color: var(--bg-color); color: var(--text-color); font-family: 'VT323', monospace; font-size: 18px; line-height: 1.6; margin: 0; padding: 20px; position: relative; overflow-x: hidden; }
        body::before { content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(transparent 50%, rgba(0, 0, 0, 0.1) 50%); background-size: 100% 4px; pointer-events: none; z-index: 1000; animation: scanlines 0.2s linear infinite; }
        @keyframes scanlines { 0% { background-position: 0 0; } 100% { background-position: 0 4px; } }
        .container { max-width: 1200px; margin: 0 auto; border: 2px solid var(--text-color); border-radius: 8px; padding: 20px; position: relative; box-shadow: 0 0 20px rgba(0, 255, 0, 0.5); background-color: rgba(0, 10, 0, 0.85); } /* Slightly different bg */
        h1, h2, h3, h4 { color: var(--accent1-color); text-shadow: 0 0 5px var(--accent1-color); border-bottom: 2px solid var(--accent2-color); padding-bottom: 5px; margin-top: 30px; }
        h1 { font-size: 42px; text-align: center; margin-bottom: 30px; animation: flicker 3s infinite; }
        @keyframes flicker { 0%, 19.999%, 22%, 62.999%, 64%, 64.999%, 70%, 100% { opacity: 1; text-shadow: 0 0 10px var(--accent1-color); } 20%, 21.999%, 63%, 63.999%, 65%, 69.999% { opacity: 0.8; text-shadow: none; } }
        pre { background-color: var(--code-bg); border: 1px solid var(--text-color); border-radius: 5px; padding: 10px; overflow-x: auto; font-family: 'Roboto Mono', monospace; font-size: 14px; }
        code { font-family: 'Roboto Mono', monospace; background-color: rgba(0, 255, 0, 0.1); padding: 2px 4px; border-radius: 3px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; font-family: 'VT323', monospace; }
        th { background-color: rgba(0, 255, 255, 0.2); border: 1px solid var(--text-color); padding: 10px; text-align: left; color: var(--accent1-color); }
        td { border: 1px solid var(--text-color); padding: 10px; word-break: break-word; }
        tr:nth-child(even) { background-color: rgba(0, 255, 0, 0.05); }
        .progress-container { width: 100%; background-color: rgba(0, 255, 0, 0.1); border-radius: 5px; margin: 10px 0; height: 20px; /* Ensure consistent height */}
        .progress-bar { height: 100%; /* Fill container */ background-color: var(--accent1-color); border-radius: 5px; transition: width 0.5s; position: relative; text-align: center; color: var(--bg-color); font-weight: bold; line-height: 20px; /* Center text vertically */ }
        .card { border: 1px solid var(--text-color); border-radius: 5px; padding: 15px; margin-bottom: 20px; background-color: var(--card-bg); box-shadow: 0 0 10px rgba(0, 255, 0, 0.2); }
        .quote { font-style: italic; color: var(--warning-color); border-left: 3px solid var(--warning-color); padding-left: 15px; margin: 20px 0; font-size: 22px; }
        .highlight { color: var(--highlight-color); font-weight: bold; text-shadow: 0 0 3px var(--highlight-color); }
        .warning { color: var(--warning-color); font-weight: bold; }
        .error { color: var(--error-color); font-weight: bold; }
        .critical { color: var(--critical-color); font-weight: bold; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { text-shadow: 0 0 5px var(--critical-color); } 50% { text-shadow: 0 0 20px var(--critical-color); } 100% { text-shadow: 0 0 5px var(--critical-color); } }
        .badge { display: inline-block; padding: 3px 10px; background-color: var(--accent2-color); color: var(--bg-color); border-radius: 10px; font-size: 14px; margin-right: 5px; }
        .stat-container { display: flex; flex-wrap: wrap; justify-content: space-between; margin: 20px 0; }
        .stat-box { flex: 1; min-width: 200px; background-color: rgba(0, 255, 0, 0.05); border: 1px solid var(--text-color); border-radius: 5px; padding: 15px; margin: 10px; text-align: center; }
        .stat-value { font-size: 36px; color: var(--accent1-color); margin: 10px 0; text-shadow: 0 0 5px var(--accent1-color); }
        .stat-label { font-size: 16px; color: var(--text-color); }
        .footer { text-align: center; margin-top: 50px; padding-top: 20px; border-top: 2px solid var(--accent2-color); font-size: 14px; color: var(--accent2-color); }
        .rickroll { position: absolute; top: 10px; right: 10px; width: 100px; height: 100px; border-radius: 50%; background: var(--accent2-color); display: flex; align-items: center; justify-content: center; animation: spin 10s linear infinite; cursor: pointer; z-index: 1001; }
        .rickroll::before { content: "RICK'S SEAL OF APPROVAL"; font-size: 10px; text-align: center; color: var(--bg-color); }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .tab-container { margin-top: 20px; }
        .tab { overflow: hidden; border: 1px solid var(--text-color); background-color: var(--code-bg); border-radius: 5px 5px 0 0; }
        .tab button { background-color: inherit; float: left; border: none; outline: none; cursor: pointer; padding: 10px 15px; transition: 0.3s; font-family: 'VT323', monospace; font-size: 18px; color: var(--text-color); }
        .tab button:hover { background-color: rgba(0, 255, 0, 0.1); }
        .tab button.active { background-color: var(--card-bg); color: var(--accent1-color); text-shadow: 0 0 5px var(--accent1-color); }
        .tabcontent { display: none; padding: 15px; border: 1px solid var(--text-color); border-top: none; border-radius: 0 0 5px 5px; background-color: var(--card-bg); }
        .issue-card { margin-bottom: 15px; border: 1px solid var(--text-color); border-radius: 5px; padding: 10px; background-color: rgba(0, 0, 0, 0.4); }
        .issue-card h4 { margin: 0 0 10px 0; border-bottom: 1px solid var(--accent2-color); padding-bottom: 5px; }
        .issue-card p { margin: 5px 0; }
        .severity-badge { float: right; padding: 3px 8px; border-radius: 5px; font-size: 14px; font-weight: bold; margin-left: 5px; } /* Added margin */
        .severity-low { background-color: #004400; color: var(--text-color); }
        .severity-medium { background-color: #444400; color: #FFFF00; }
        .severity-high { background-color: #440000; color: var(--error-color); }
        .severity-critical { background-color: #440044; color: var(--critical-color); animation: pulse 2s infinite; }
        .severity-unknown { background-color: #333333; color: #aaaaaa; } /* Added unknown severity */
        .metrics-chart { height: 300px; background-color: rgba(0, 0, 0, 0.4); border-radius: 5px; margin: 20px 0; position: relative; padding: 10px; box-sizing: border-box;} /* Added padding */
        .file-browser { height: 400px; overflow: auto; background-color: var(--code-bg); border: 1px solid var(--text-color); border-radius: 5px; padding: 10px; font-family: 'Roboto Mono', monospace; font-size: 14px; }
        .file-browser ul { list-style-type: none; padding: 0; margin: 0; }
        .file-browser li { padding: 3px 10px; margin: 2px 0; cursor: pointer; border-radius: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; } /* Added text overflow */
        .file-browser li:hover { background-color: rgba(0, 255, 0, 0.1); }
        .file-browser .file-issues { margin-left: 5px; padding: 0 5px; background-color: var(--warning-color); color: black; border-radius: 10px; font-size: 12px; display: inline-block;} /* Added display */
        .file-browser .folder::before { content: "📁 "; }
        .file-browser .file::before { content: "📄 "; }
        .recommendations { list-style-type: none; padding: 0; }
        .recommendations li { margin-bottom: 15px; padding: 10px; background-color: rgba(0, 0, 0, 0.4); border: 1px solid var(--text-color); border-radius: 5px; position: relative; }
        .recommendations li::before { content: "💡"; margin-right: 10px; font-size: 20px; position: absolute; top: 10px; left: 10px; } /* Positioned icon */
        .recommendations li { padding-left: 40px; } /* Added padding for icon */
        .code-context { background-color: var(--code-bg); padding: 10px; border-radius: 5px; margin-top: 10px; font-family: 'Roboto Mono', monospace; font-size: 14px; overflow-x: auto; }
        #dependencyGraphContainer { position: relative; }
        #dependencyGraphContainer .vis-network { outline: none; }
        .error-box { border: 2px solid var(--error-color); background-color: rgba(255,0,0,0.1); padding: 10px; margin-top: 10px; color: var(--error-color); }
        @media (max-width: 768px) { .stat-container { flex-direction: column; } .stat-box { margin: 5px 0; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="rickroll" onclick="alert('Never gonna give your code up, never gonna let your code down!')"></div>
        <h1>Rick's Advanced Code Analysis Report</h1>

        <!-- Project Quality Summary Card -->
        <div class="card">
             <h2>Project Quality Summary</h2>
             <div class="stat-container">
                 <div class="stat-box"><div class="stat-label">Maintainability</div><div class="stat-value">{{ maintainability_score }}/100</div><div>{{ maintainability_rating }}</div></div>
                 <div class="stat-box"><div class="stat-label">Technical Debt</div><div class="stat-value">{{ technical_debt_days }}</div><div>days to fix</div></div>
                 <div class="stat-box"><div class="stat-label">Code Issues</div><div class="stat-value">{{ total_issues }}</div><div>problems found</div></div>
                 <div class="stat-box"><div class="stat-label">Files Analyzed</div><div class="stat-value">{{ total_files }}</div><div>{{ total_lines_of_code }} lines</div></div>
             </div>
             <div class="quote">{{ rick_quote }}</div>
             <p>Project: <span class="highlight">{{ project_path }}</span></p>
             <p>Analysis Date: <span class="highlight">{{ analysis_date }}</span></p>
        </div>

        <!-- Project Metrics Card -->
        <div class="card" id="project-metrics-card">
            <h2>Project Metrics</h2>
            <div class="tab">
                <button class="tablinks active" onclick="openTab(event, 'OverallMetrics', 'project-metrics-card')">Overview</button>
                <button class="tablinks" onclick="openTab(event, 'LanguageStats', 'project-metrics-card')">Languages</button>
                <button class="tablinks" onclick="openTab(event, 'ComplexityMetrics', 'project-metrics-card')">Complexity</button>
                <button class="tablinks" onclick="openTab(event, 'FileMetrics', 'project-metrics-card')">Files</button>
            </div>
            <div id="OverallMetrics" class="tabcontent" style="display: block;">
                <div class="metrics-chart" id="overallChart">
                    <canvas id="overallCanvasElement"></canvas>
                </div>
                <div class="stat-container">
                    <div class="stat-box"><div class="stat-label">Total Code Lines</div><div class="stat-value">{{ code_lines }}</div></div>
                    <div class="stat-box"><div class="stat-label">Comment Density</div><div class="stat-value">{{ comment_density }}%</div></div>
                    <div class="stat-box"><div class="stat-label">Avg Fn Complexity</div><div class="stat-value">{{ avg_function_complexity }}</div></div>
                    <div class="stat-box"><div class="stat-label">Duplicated Blocks</div><div class="stat-value">{{ duplicated_blocks }}</div></div>
                </div>
            </div>
            <div id="LanguageStats" class="tabcontent">
                 <table>
                    <thead><tr><th>Language</th><th>Files</th><th>Percentage</th></tr></thead>
                    <tbody>
                        {% for lang in language_stats %}
                        <tr><td>{{ lang.language }}</td><td>{{ lang.count }}</td><td>{{ lang.percentage }}%</td></tr>
                        {% else %}
                        <tr><td colspan="3">No language data available.</td></tr>
                        {% endfor %}
                    </tbody>
                 </table>
                 <div class="metrics-chart" id="languageChart">
                    <canvas id="languageCanvasElement"></canvas>
                 </div>
            </div>
            <div id="ComplexityMetrics" class="tabcontent">
                 <div class="stat-container">
                    <div class="stat-box"><div class="stat-label">Avg Function Size</div><div class="stat-value">{{ avg_function_size }}</div><div>lines</div></div>
                    <div class="stat-box"><div class="stat-label">Avg Parameters</div><div class="stat-value">{{ avg_function_params }}</div></div>
                    <div class="stat-box"><div class="stat-label">Maintainability</div><div class="stat-value">{{ maintainability_score }}/100</div></div>
                    <div class="stat-box"><div class="stat-label">Technical Debt</div><div class="stat-value">{{ technical_debt_days }}</div><div>days</div></div>
                 </div>
                 <div class="metrics-chart" id="complexityChart">
                     <canvas id="complexityCanvasElement"></canvas>
                 </div>
            </div>
            <div id="FileMetrics" class="tabcontent">
                 <h3>Largest Files (by lines)</h3>
                 <table>
                     <thead><tr><th>File Name</th><th>Lines</th><th>Language</th></tr></thead>
                     <tbody>
                         {% for file in largest_files %}
                         <tr><td>{{ file.name }}</td><td>{{ file.lines }}</td><td>{{ file.language }}</td></tr>
                         {% else %}
                         <tr><td colspan="3">No file data available.</td></tr>
                         {% endfor %}
                     </tbody>
                 </table>
            </div>
        </div>

        <!-- Issues Found Card -->
        <div class="card" id="issues-found-card">
            <h2>Issues Found ({{ total_issues }})</h2>
            <div class="tab">
                <button class="tablinks active" onclick="openTab(event, 'CodeSmells', 'issues-found-card')">Code Smells ({{ code_smell_count }})</button>
                <button class="tablinks" onclick="openTab(event, 'SecurityIssues', 'issues-found-card')">Security ({{ security_issue_count }})</button>
                <button class="tablinks" onclick="openTab(event, 'PerformanceIssues', 'issues-found-card')">Performance ({{ performance_issue_count }})</button>
                <button class="tablinks" onclick="openTab(event, 'StyleIssues', 'issues-found-card')">Style ({{ style_issue_count }})</button>
                <button class="tablinks" onclick="openTab(event, 'DuplicatedCode', 'issues-found-card')">Duplications ({{ duplicated_blocks }})</button>
            </div>
            <div id="CodeSmells" class="tabcontent" style="display: block;">
                 {% if code_smells %}{% for file_path, issues in code_smells.items() %}<div class="issue-card"><h4>{{ file_path | replace(project_path + '\\\\', '') | replace(project_path + '/', '') }}</h4>{% for issue in issues %}<p><span class="severity-badge severity-{{ issue.severity | lower }}">{{ issue.severity | capitalize }}</span> Line {{ issue.line }}: {{ issue.description }}</p>{% if issue.context %}<div class="code-context"><pre><code>{{ issue.context | escape }}</code></pre></div>{% endif %}{% endfor %}</div>{% else %}<p>No code smells detected. Nice!</p>{% endfor %}{% else %}<p>No code smells detected.</p>{% endif %}
            </div>
            <div id="SecurityIssues" class="tabcontent">
                 {% if security_issues %}{% for file_path, issues in security_issues.items() %}<div class="issue-card"><h4>{{ file_path | replace(project_path + '\\\\', '') | replace(project_path + '/', '') }}</h4>{% for issue in issues %}<p><span class="severity-badge severity-{{ issue.severity | lower }}">{{ issue.severity | capitalize }}</span> Line {{ issue.line }}: {{ issue.description }}</p>{% if issue.context %}<div class="code-context"><pre><code>{{ issue.context | escape }}</code></pre></div>{% endif %}{% endfor %}</div>{% else %}<p>No security issues detected. Keep it up!</p>{% endfor %}{% else %}<p>No security issues detected.</p>{% endif %}
            </div>
            <div id="PerformanceIssues" class="tabcontent">
                 {% if performance_issues %}{% for file_path, issues in performance_issues.items() %}<div class="issue-card"><h4>{{ file_path | replace(project_path + '\\\\', '') | replace(project_path + '/', '') }}</h4>{% for issue in issues %}<p><span class="severity-badge severity-{{ issue.severity | lower }}">{{ issue.severity | capitalize }}</span> Line {{ issue.line }}: {{ issue.description }}</p>{% if issue.context %}<div class="code-context"><pre><code>{{ issue.context | escape }}</code></pre></div>{% endif %}{% endfor %}</div>{% else %}<p>No performance issues detected.</p>{% endfor %}{% else %}<p>No performance issues detected.</p>{% endif %}
            </div>
            <div id="StyleIssues" class="tabcontent">
                 {% if style_issues %}{% for file_path, issues in style_issues.items() %}<div class="issue-card"><h4>{{ file_path | replace(project_path + '\\\\', '') | replace(project_path + '/', '') }}</h4>{% for issue in issues %}<p><span class="severity-badge severity-{{ issue.severity | lower }}">{{ issue.severity | capitalize }}</span> Line {{ issue.line }}: {{ issue.description }}</p>{% if issue.context %}<div class="code-context"><pre><code>{{ issue.context | escape }}</code></pre></div>{% endif %}{% endfor %}</div>{% else %}<p>No style issues detected.</p>{% endfor %}{% else %}<p>No style issues detected.</p>{% endif %}
            </div>
            <div id="DuplicatedCode" class="tabcontent">
                {% if duplicated_code %}
                    <p>Found {{ duplicated_code | length }} duplicated code blocks:</p>
                    {% for block in duplicated_code %}
                        <div class="issue-card">
                            <h4>Duplication found across {{ block.files | length }} locations</h4>
                            <p><span class="highlight">Lines:</span> {{ block.lines }} | <span class="highlight">Tokens:</span> {{ block.tokens }}</p>
                            <p><span class="highlight">Locations:</span></p>
                            <ul style="list-style-type: square; margin-left: 20px;">
                            {% for loc in block.files %}
                                <li>{{ loc.file_path | replace(project_path + '\\\\', '') | replace(project_path + '/', '') }} (Lines {{ loc.start_line }} - {{ loc.end_line }})</li>
                            {% endfor %}
                            </ul>
                            <p><span class="highlight">Code Snippet (first 10 lines):</span></p>
                            <div class="code-context"><pre><code>{{ block.code_snippet | escape }}</code></pre></div>
                        </div>
                    {% endfor %}
                {% else %}
                    <p>No significant duplicated code blocks detected.</p>
                {% endif %}
            </div>
        </div>

        <!-- Dependency Security Scan Results Card -->
        {% if dependency_scan %}
        <div class="card">
            <h2>Dependency Security Scan (Safety)</h2>
            <p>Status: <span class="{{ 'error' if dependency_scan.status == 'Vulnerable' else ('warning' if dependency_scan.status == 'Error' else 'highlight') }}">{{ dependency_scan.status }}</span></p> {# Added warning class for error status #}
            {% if dependency_scan.status == 'Vulnerable' %}
                <p class="warning">Found {{ dependency_scan.vulnerabilities | length }} vulnerable dependencies:</p>
                <table>
                    <thead><tr><th>Package</th><th>Version</th><th>Affected</th><th>ID</th><th>Description</th></tr></thead>
                    <tbody>
                    {% for vuln in dependency_scan.vulnerabilities %}
                        <tr>
                            <td>{{ vuln.package }}</td>
                            <td>{{ vuln.installed_version }}</td>
                            <td>{{ vuln.affected_versions }}</td>
                            <td><a href="https://security.snyk.io/vuln/{{ vuln.vuln_id }}" target="_blank" style="color: var(--accent1-color);">{{ vuln.vuln_id }}</a></td> {# Made ID a link #}
                            <td>{{ vuln.description }}</td>
                        </tr>
                    {% else %}
                         <tr><td colspan="5">Vulnerability data seems empty.</td></tr>
                    {% endfor %}
                    </tbody>
                </table>
            {% elif dependency_scan.status == 'Error' %}
                 <p class="error">Error during scan: {{ dependency_scan.error }}</p>
                 {% if dependency_scan.details %}<pre style="max-height: 150px; overflow-y: auto;">{{ dependency_scan.details }}</pre>{% endif %} {# Added scrollable pre for details #}
            {% elif dependency_scan.status == 'Not Run' %}
                 <p>Scan was not executed.</p>
            {% elif dependency_scan.status == 'No Requirements' %}
                 <p>No Python requirement files (requirements.txt, pyproject.toml[tool.poetry.dependencies]) found to scan.</p>
            {% else %} {# Secure or other status #}
                 <p>No known vulnerabilities found in scanned dependencies.</p>
            {% endif %}
        </div>
        {% endif %}

        <!-- ***** NEW: Encoding Stats Card ***** -->
        {% if encoding_stats %}
        <div class="card">
            <h2>File Encoding Distribution</h2>
            <p>Detected encodings across analyzed files. Inconsistencies might cause *burp* weirdness.</p>
            <table>
                <thead>
                    <tr>
                        <th>Encoding Type</th>
                        <th>File Count</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
                    {% for stat in encoding_stats %}
                    <tr>
                        <td>{{ stat.encoding if stat.encoding else 'Unknown/Binary?' }}</td>
                        <td>{{ stat.count }}</td>
                        <td>
                            <div class="progress-container">
                                <div class="progress-bar" style="width: {{ stat.percentage }}%" title="{{ stat.percentage }}%">{{ stat.percentage }}%</div>
                            </div>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="3">No encoding data collected or available.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <p style="font-size: 12px; text-align: center; margin-top: 10px;">(Based on initial bytes detected by chardet)</p>
        </div>
        {% endif %}
        <!-- ***** END: Encoding Stats Card ***** -->

        <!-- Dependency Visualization Card -->
        {% if dependency_graph and dependency_graph.nodes %}
        <div class="card">
            <h2>Internal Dependency Graph</h2>
            <p>Visualizing imports between analyzed project files. (External libraries excluded).</p>
            <div id="dependencyGraphContainer" style="height: 600px; border: 1px solid var(--text-color); background-color: rgba(0,0,0,0.2); border-radius: 5px; position: relative;">
                 <div id="graphLoadingMsg" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: var(--text-color); font-size: 18px; text-align: center;">Loading Graph...</div>
                 <div id="graphErrorMsg" class="error-box" style="display: none; position: absolute; top: 10px; left: 10px; right: 10px; z-index: 10;"></div> {# Positioned error message #}
            </div>
            <p style="font-size: 14px; text-align: center; margin-top: 10px;">(Scroll to zoom, drag nodes to rearrange, use navigation buttons)</p> {# Added mention of buttons #}
        </div>
        {% endif %}

        <!-- Code Browser Card -->
        <div class="card" id="code-browser-card">
             <h2>Code Browser</h2>
             <div class="tab">
                <button class="tablinks active" onclick="openTab(event, 'FileBrowser', 'code-browser-card')">Files</button>
             </div>
             <div id="FileBrowser" class="tabcontent" style="display: block;">
                  <div class="file-browser">
                    <ul>
                        {% for file in file_tree %}
                        <li class="{{ file.type }}" onclick="showFileDetails('{{ file.path | escape }}')" title="{{ file.path }}"> {# Added title attribute #}
                            {{ file.name }}
                            {% if file.issues > 0 %}<span class="file-issues">{{ file.issues }}</span>{% endif %}
                        </li>
                        {% else %}
                        <li>No files found or analyzed.</li>
                        {% endfor %}
                    </ul>
                  </div>
                  <div id="fileDetails" style="display: none; margin-top: 15px; padding: 10px; background-color: rgba(0,0,0,0.3); border-radius: 5px;">
                    <h3 id="fileDetailsName" style="margin-top:0;"></h3>
                    <div id="fileDetailsInfo"></div> {# Changed p to div for easier innerHTML update #}
                    <div id="fileDetailsIssues"></div>
                    {# Code display handled by JS based on pygmentsAvailable #}
                    <pre id="fileDetailsCode" style="max-height: 300px; overflow-y: auto; display: none;"></pre> {# Initially hidden #}
                    <p id="fileDetailsCodePlaceholder" style="font-size: 14px; display: none;"></p> {# Initially hidden #}
                 </div>
            </div>
        </div>

        <!-- Recommendations Card -->
        <div class="card">
             <h2>Recommendations</h2>
             <ul class="recommendations">
                 {% for rec in recommendations %}<li>{{ rec }}</li>{% else %}<li>No specific recommendations generated. Looks good or analysis was limited.</li>{% endfor %}
             </ul>
        </div>

        <!-- Best Practices Card -->
        {% if best_practices %}
        <div class="card" id="best-practices-card">
             <h2>Best Practices Checklist</h2> {# Changed title slightly #}
             <div class="tab">
                 {% for lang in best_practices.keys() %}
                 <button class="tablinks {% if loop.first %}active{% endif %}" onclick="openTab(event, 'BestPractices{{ lang|replace('+','Plus')|replace('#','Sharp')|capitalize }}', 'best-practices-card')">
                     {{ lang|capitalize }}
                 </button>
                 {% else %}
                 <span>No best practice data available.</span>
                 {% endfor %}
             </div>
             {% for lang, practices in best_practices.items() %}
             <div id="BestPractices{{ lang|replace('+','Plus')|replace('#','Sharp')|capitalize }}" class="tabcontent" {% if loop.first %}style="display: block;"{% endif %}>
                 <ul>{% for p in practices %}<li>{{ p }}</li>{% else %}<li>No specific best practices listed for {{ lang | capitalize }}.</li>{% endfor %}</ul>
             </div>
             {% endfor %}
        </div>
        {% endif %}

        <!-- Footer -->
        <div class="footer">
             <p>Generated by Rick's Advanced Code Analyzer © {{ current_year }} Wubba Lubba Dub Dub Inc.</p>
             <p>If this analysis seems wrong, remember that *burp* in an infinite multiverse, there's one where it's right.</p>
        </div>
    </div>

    <script>
        // ***** Corrected openTab Function *****
        function openTab(event, tabName, cardId) {
            var i, tabcontent, tablinks;
            var parentCard = document.getElementById(cardId);

            if (!parentCard) {
                console.error("Cannot find parent card with ID:", cardId);
                parentCard = event.currentTarget.closest('.card'); // Fallback
                if (!parentCard) { console.error("Could not find parent card via closest."); return; }
            }

            tabcontent = parentCard.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) { tabcontent[i].style.display = "none"; }

            tablinks = parentCard.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) { tablinks[i].className = tablinks[i].className.replace(" active", ""); }

            var targetTab = document.getElementById(tabName); // Use global ID lookup
            if (targetTab) {
                 if (parentCard.contains(targetTab)) {
                      targetTab.style.display = "block";
                      event.currentTarget.className += " active";
                 } else {
                      console.error("Target tab #" + tabName + " found, but not within expected card #" + cardId);
                 }
            } else { console.error("Target tab element not found by ID:", tabName); }
        }

        // Retro terminal effects
        document.addEventListener('DOMContentLoaded', function() {
             try {
                 setInterval(function() {
                     const elements = document.querySelectorAll('h1, h2, h3, .stat-value');
                     if (elements.length > 0) {
                         const randomElement = elements[Math.floor(Math.random() * elements.length)];
                         if (randomElement) { randomElement.style.opacity = '0.5'; setTimeout(function() { if(randomElement) randomElement.style.opacity = '1'; }, 100); }
                     }
                 }, 3000);
             } catch(err) { console.error("Error in glitch effect:", err); }
        });

        // --- Injected Dynamic JS Placeholder ---
        // (This comment will be replaced by the JS generated in Python)
        // --- End Injected Dynamic JS Placeholder ---

    </script>
</body>
</html>
'''


class AdvancedReporter:
    """Advanced report generation for Rick's Code Analyzer"""

    def __init__(self, callback_function=None):
        self.callback = callback_function

    def update_progress(self, message):
        if self.callback: self.callback(message)
        else: print(message)

    def generate_report(self, project_path, basic_analysis, advanced_analysis, extras_results=None):
        # (Keep the generate_report method from v4.2 - it was correct)
        self.update_progress("Generating advanced HTML report...")
        file_path = None
        global REPORT_PACKAGES_AVAILABLE # Access global flag

        if not REPORT_PACKAGES_AVAILABLE:
            self.update_progress("Error: jinja2 is required for report generation.")
            return None

        try:
            import jinja2 # Import here is fine now check is done
            self.update_progress("DEBUG: Jinja2 imported successfully.")

            try:
                 report_dir = tempfile.mkdtemp(prefix="ricks_analyzer_")
                 self.update_progress(f"DEBUG: Created temporary directory: {report_dir}")
            except Exception as e_dir:
                 self.update_progress(f"ERROR: Failed to create temp directory: {e_dir}")
                 return None

            project_name = os.path.basename(project_path) if project_path and isinstance(project_path, str) else "report"
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in ('_', '-')).rstrip()
            file_path = os.path.join(report_dir, f"rick_advanced_report_{safe_project_name}_{timestamp}.html")
            self.update_progress(f"DEBUG: Report file path set to: {file_path}")

            template_data = self._prepare_template_data(project_path, basic_analysis, advanced_analysis, extras_results)
            if not template_data:
                self.update_progress("ERROR: Failed to prepare template data. Report generation aborted.")
                return None
            self.update_progress("DEBUG: Template data prepared successfully.")

            template_env = jinja2.Environment(
                loader=jinja2.BaseLoader(),
                autoescape=jinja2.select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )
            template = template_env.from_string(HTML_REPORT_TEMPLATE)
            self.update_progress("DEBUG: Rendering HTML content...")
            html_content = template.render(**template_data)
            self.update_progress(f"DEBUG: HTML content rendered (length: {len(html_content)}).")

            self.update_progress("DEBUG: Adding dynamic JavaScript...")
            html_content = self._add_dynamic_javascript(html_content, template_data)
            self.update_progress(f"DEBUG: Dynamic JavaScript added (new length: {len(html_content)}).")

            self.update_progress(f"DEBUG: Writing HTML to file: {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f: f.write(html_content)
            self.update_progress("DEBUG: HTML file written successfully.")

            self.update_progress(f"Advanced HTML report generation successful: {file_path}")
            return file_path

        except jinja2.exceptions.TemplateError as e:
             error_line = getattr(e, 'lineno', 'N/A')
             error_msg = getattr(e, 'message', str(e))
             self.update_progress(f"ERROR: Jinja2 Template Error (Line: {error_line}): {error_msg}")
             if file_path and os.path.exists(file_path):
                 try: os.remove(file_path)
                 except OSError: pass
             return None
        except Exception as e:
            self.update_progress(f"Error during advanced report generation: {str(e)}")
            self.update_progress(traceback.format_exc())
            if file_path and os.path.exists(file_path):
                try: os.remove(file_path)
                except OSError: pass
            return None

    # --- _prepare_template_data method ---
    # (Keep the previously corrected _prepare_template_data method from v4.2)
    def _prepare_template_data(self, project_path, basic_analysis, advanced_analysis, extras_results=None):
        """Prepare data for the HTML template."""
        _QUALITY_RATINGS = globals().get('QUALITY_RATINGS', {})
        _RICK_QUOTES = globals().get('RICK_QUOTES', ["Wubba lubba dub dub!"])
        if not _QUALITY_RATINGS or not isinstance(_QUALITY_RATINGS, dict):
            self.update_progress("ERROR: QUALITY_RATINGS global variable not found or is not a valid dictionary in advanced_reporter.py.")
            return None
        default_quotes = _RICK_QUOTES if isinstance(_RICK_QUOTES, list) and _RICK_QUOTES else ["Wubba lubba dub dub!"]
        try:
            project_path_norm = os.path.normpath(project_path) if project_path and isinstance(project_path, str) else ""
            metrics = advanced_analysis.get('complexity_metrics', {})
            maintainability_score = round(metrics.get('maintainability_index', 0))
            rating = "Unknown"
            quotes = default_quotes
            if maintainability_score >= 80: rating, quotes = "Excellent", _QUALITY_RATINGS.get('excellent', default_quotes)
            elif maintainability_score >= 60: rating, quotes = "Good", _QUALITY_RATINGS.get('good', default_quotes)
            elif maintainability_score >= 40: rating, quotes = "Fair", _QUALITY_RATINGS.get('fair', default_quotes)
            elif maintainability_score >= 20: rating, quotes = "Poor", _QUALITY_RATINGS.get('poor', default_quotes)
            else: rating, quotes = "Very Poor", _QUALITY_RATINGS.get('very_poor', default_quotes)
            rick_quote = random.choice(quotes) if isinstance(quotes, list) and quotes else random.choice(default_quotes)
            code_smell_count = sum(len(v) for v in advanced_analysis.get('code_smells', {}).values())
            security_issue_count = sum(len(v) for v in advanced_analysis.get('security_issues', {}).values())
            performance_issue_count = sum(len(v) for v in advanced_analysis.get('performance_issues', {}).values())
            style_issue_count = sum(len(v) for v in advanced_analysis.get('style_issues', {}).values())
            duplicated_code_data = advanced_analysis.get('duplicated_code', [])
            duplicated_blocks_count = len(duplicated_code_data) if isinstance(duplicated_code_data, list) else 0
            total_issues = code_smell_count + security_issue_count + performance_issue_count + style_issue_count
            language_stats = []
            total_files_basic = basic_analysis.get('total_files_analyzed', 1) or 1 # Default to 1 to avoid division by zero
            for lang, count in basic_analysis.get('language_stats', {}).items():
                percentage = round((count / total_files_basic) * 100, 1)
                language_stats.append({'language': lang, 'count': count, 'percentage': percentage})
            language_stats.sort(key=lambda x: x['count'], reverse=True)
            file_stats = basic_analysis.get('file_stats', {})
            all_issues_by_file = defaultdict(lambda: defaultdict(list))
            issue_categories = ['code_smells', 'security_issues', 'performance_issues', 'style_issues']
            encoding_stats_raw = basic_analysis.get('encoding_stats', {})
            encoding_stats_list = []
            if encoding_stats_raw and isinstance(encoding_stats_raw, dict):
                # Convert dict/Counter to list of dicts for easier sorting/rendering
                total_enc_files = sum(encoding_stats_raw.values()) or 1  # Avoid division by zero
                encoding_stats_list = [
                    {'encoding': enc, 'count': count, 'percentage': round((count / total_enc_files) * 100, 1)}
                    for enc, count in encoding_stats_raw.items()
                ]
                # Sort by count descending
                encoding_stats_list.sort(key=lambda x: x['count'], reverse=True)
            for fs_path in file_stats:
                 if isinstance(file_stats[fs_path], dict): file_stats[fs_path]['issues'] = file_stats[fs_path].get('issues', 0)
            for category in issue_categories:
                for file_path, issues in advanced_analysis.get(category, {}).items():
                    normalized_issue_file_path = os.path.normpath(file_path)
                    matched_fs_key = None
                    for fs_key in file_stats.keys():
                        if os.path.normpath(fs_key) == normalized_issue_file_path: matched_fs_key = fs_key; break
                    if matched_fs_key and isinstance(file_stats[matched_fs_key], dict):
                         file_stats[matched_fs_key]['issues'] += len(issues)
                         all_issues_by_file[matched_fs_key][category].extend(issues)
                    else: self.update_progress(f"DEBUG: Issue file path '{normalized_issue_file_path}' not found/invalid in basic file_stats.")
            largest_files = sorted([{'name': os.path.basename(p), **s} for p, s in file_stats.items() if isinstance(s, dict) and 'lines' in s], key=lambda x: x.get('lines', 0), reverse=True)[:10]
            file_tree = []
            processed_paths_for_tree = set()
            for file_path_key, stats in file_stats.items():
                if not isinstance(stats, dict): continue
                norm_path = os.path.normpath(file_path_key)
                if norm_path in processed_paths_for_tree: continue
                processed_paths_for_tree.add(norm_path)
                display_path = os.path.basename(norm_path)
                try:
                    if project_path_norm and norm_path.startswith(project_path_norm): display_path = os.path.relpath(norm_path, project_path_norm)
                except (ValueError, TypeError): pass
                file_tree.append({'name': stats.get('name', os.path.basename(file_path_key)), 'path': display_path.replace(os.sep, '/'), 'type': 'file', 'issues': stats.get('issues', 0), 'language': stats.get('language', 'Unknown')})
            file_tree.sort(key=lambda x: (x['issues'], x['path']), reverse=True)
            recommendations = advanced_analysis.get('recommendations', [])
            if not recommendations and isinstance(recommendations, list):
                if maintainability_score < 60: recommendations.append("Improve overall code maintainability (score is low).")
                if metrics.get('comment_density', 0) < 0.1: recommendations.append("Increase code documentation (comment density is low).")
                if security_issue_count > 0: recommendations.append("Address detected security vulnerabilities.")
                if total_issues > 50: recommendations.append("Prioritize fixing the high number of detected code issues.")
                if not recommendations: recommendations.append("Code looks relatively clean based on available metrics!")
            dependency_scan_data = extras_results.get('dependency_scan') if extras_results else None
            dependency_graph_data = extras_results.get('dependency_graph') if extras_results else None
            file_details_for_json = {}
            for item in file_tree:
                original_full_path = None; stats = None; found = False
                tree_item_path_reconstructed = os.path.normpath(os.path.join(project_path_norm, item['path'].replace('/', os.sep))) if project_path_norm else item['path']
                for fs_key, fs_data in file_stats.items():
                     if not isinstance(fs_data, dict): continue
                     if os.path.normpath(fs_key) == tree_item_path_reconstructed: original_full_path = fs_key; stats = fs_data; found = True; break
                if not found:
                     for fs_key, fs_data in file_stats.items():
                         if not isinstance(fs_data, dict): continue
                         if fs_data.get('name') == item['name']: original_full_path = fs_key; stats = fs_data; found = True; break
                if found and original_full_path and stats:
                     display_path_key = item['path']
                     file_details_for_json[display_path_key] = {'name': stats.get('name', 'Unknown'), 'language': stats.get('language', 'Unknown'), 'lines': stats.get('lines', 0), 'code': stats.get('code', 0), 'comments': stats.get('comments', 0), 'blank': stats.get('blank', 0), 'all_issues': all_issues_by_file.get(original_full_path, {})}
                else: self.update_progress(f"DEBUG: Could not map file_tree item '{item['path']}' back to original file_stat entry.")
            template_data = {
                'project_path': project_path_norm, 'analysis_date': advanced_analysis.get('analysis_metadata', {}).get('timestamp', datetime.datetime.now().isoformat()),
                'maintainability_score': maintainability_score, 'maintainability_rating': rating, 'technical_debt_days': round(metrics.get('technical_debt_days', 0), 1),
                'total_issues': total_issues, 'total_files': basic_analysis.get('total_files', 0), 'total_lines_of_code': metrics.get('total_lines_of_code', 0),
                'code_lines': basic_analysis.get('code_lines', 0), 'comment_lines': basic_analysis.get('comment_lines', 0), 'comment_density': round(metrics.get('comment_density', 0) * 100, 1),
                'function_count': len(advanced_analysis.get('function_metrics', {})), 'avg_function_complexity': round(metrics.get('avg_function_complexity', 0), 1),
                'avg_function_size': round(metrics.get('avg_function_size', 0), 1), 'avg_function_params': round(metrics.get('avg_function_params', 0), 1),
                'duplicated_blocks': duplicated_blocks_count, 'language_stats': language_stats, 'largest_files': largest_files, 'file_tree': file_tree,
                'code_smell_count': code_smell_count, 'security_issue_count': security_issue_count, 'performance_issue_count': performance_issue_count, 'style_issue_count': style_issue_count,
                'code_smells': advanced_analysis.get('code_smells', {}), 'security_issues': advanced_analysis.get('security_issues', {}), 'performance_issues': advanced_analysis.get('performance_issues', {}), 'style_issues': advanced_analysis.get('style_issues', {}),
                'duplicated_code': duplicated_code_data, 'recommendations': recommendations, 'best_practices': advanced_analysis.get('best_practices', {}),
                'rick_quote': rick_quote, 'current_year': datetime.datetime.now().year, 'pygments_available': PYGMENTS_AVAILABLE,
                'dependency_scan': dependency_scan_data, 'dependency_graph': dependency_graph_data, 'file_details_json': json.dumps(file_details_for_json),
                'encoding_stats': encoding_stats_list
            }
            return template_data
        except Exception as e:
            self.update_progress(f"ERROR during _prepare_template_data logic: {e}")
            self.update_progress(traceback.format_exc())
            return None

    # --- _add_dynamic_javascript method ---
    # (Keep the previously corrected _add_dynamic_javascript method from v4.2)
    def _add_dynamic_javascript(self, html_content, template_data):
        all_js_parts = []
        js_wrapper_start = "\n// --- Injected Dynamic JS ---\ndocument.addEventListener('DOMContentLoaded', function() {\ntry {\n"
        js_wrapper_end = "\n} catch (err) { console.error('Error in injected JS DOMContentLoaded:', err); }\n}); // End DOMContentLoaded\n// --- End Injected Dynamic JS ---"
        try:
            chart_js = self._generate_charts_js(template_data)
            if chart_js: all_js_parts.append(chart_js)
            file_details_js = self._generate_file_details_js(template_data)
            if file_details_js: all_js_parts.append(file_details_js)
            graph_js = self._generate_graph_js(template_data)
            if graph_js: all_js_parts.append(graph_js)
        except Exception as e:
            self.update_progress(f"ERROR generating dynamic JS content string: {e}")
            error_message = str(e).replace('`', '\\`').replace("'", "\\'").replace('\n', '\\n').replace('"','\\"')
            all_js_parts.append(f"console.error('Error generating report JavaScript (Python): {error_message}');")
        final_js = js_wrapper_start + "\n".join(all_js_parts) + js_wrapper_end
        placeholder_comment = "// --- Injected Dynamic JS Placeholder ---"
        placeholder_end_comment = "// --- End Injected Dynamic JS Placeholder ---"
        start_index = html_content.find(placeholder_comment)
        end_index = html_content.find(placeholder_end_comment)
        if start_index != -1 and end_index != -1:
             html_content = html_content[:start_index] + final_js + html_content[end_index + len(placeholder_end_comment):]
        else:
             insert_pos = html_content.rfind('</body>')
             if insert_pos > 0: html_content = html_content[:insert_pos] + f"<script>{final_js}</script>\n" + html_content[insert_pos:]
             else: html_content += f"<script>{final_js}</script>"
             self.update_progress("Warning: Could not find JS placeholder comment block. Appended JS.")
        return html_content


    # --- *** CORRECTED JS GENERATION METHODS *** ---

    def _generate_charts_js(self, template_data):
        """Generate JavaScript code for canvas charts, fully escaped for f-string."""
        try:
            # (Data extraction logic remains the same as v4.2)
            code_smell_count = int(template_data.get('code_smell_count', 0))
            security_issue_count = int(template_data.get('security_issue_count', 0))
            performance_issue_count = int(template_data.get('performance_issue_count', 0))
            style_issue_count = int(template_data.get('style_issue_count', 0))
            language_stats_list = template_data.get('language_stats', [])[:5]
            pie_chart_data = [
                { "label": 'Smells', "value": code_smell_count }, { "label": 'Security', "value": security_issue_count },
                { "label": 'Perf', "value": performance_issue_count }, { "label": 'Style', "value": style_issue_count },
            ]
            non_zero_pie_data = [item for item in pie_chart_data if item["value"] > 0]
            final_pie_data = non_zero_pie_data if non_zero_pie_data else pie_chart_data
            pie_data_js = json.dumps(final_pie_data)
            lang_data_list = []
            for lang in language_stats_list:
                label = str(lang.get("language","?")).replace("'", "\\'")[:15]
                value = int(lang.get("count",0))
                if value > 0: lang_data_list.append({ "label": label, "value": value })
            lang_data_js = json.dumps(lang_data_list)
            maintainability_score = int(template_data.get('maintainability_score', 0))
            avg_complexity_val = float(template_data.get('avg_function_complexity', 0))
            avg_complexity_bar = max(1, int(avg_complexity_val))
            avg_size_val = float(template_data.get('avg_function_size', 0))
            avg_size_bar = max(1, int(avg_size_val))
            debt_days_val = float(template_data.get('technical_debt_days', 0))
            debt_days_bar = max(1, int(debt_days_val))
            complexity_data_js = json.dumps([
                 { "label": 'Maintain.', "value": max(1, maintainability_score), "origValue": maintainability_score },
                 { "label": 'Avg Comp.', "value": avg_complexity_bar, "origValue": round(avg_complexity_val,1) },
                 { "label": 'Avg Size', "value": avg_size_bar, "origValue": round(avg_size_val,1) },
                 { "label": 'Debt Days', "value": debt_days_bar, "origValue": round(debt_days_val,1) }
             ])

            # *** F-STRING WITH DOUBLED BRACES for JS code ***
            js_code = f"""
            // --- Charts JS ---
            (function() {{ // IIFE Wrapper - Double Braces
                console.log("Initializing charts...");
                const chartTextColor = getComputedStyle(document.documentElement).getPropertyValue('--text-color') || '#00FF00';
                const chartAccent1 = getComputedStyle(document.documentElement).getPropertyValue('--accent1-color') || '#00FFFF';
                const chartAccent2 = getComputedStyle(document.documentElement).getPropertyValue('--accent2-color') || '#FF00FF';
                const chartErrorColor = getComputedStyle(document.documentElement).getPropertyValue('--error-color') || '#FF0000';
                const chartWarningColor = getComputedStyle(document.documentElement).getPropertyValue('--warning-color') || '#FF6000';
                const chartHighlightColor = getComputedStyle(document.documentElement).getPropertyValue('--highlight-color') || '#39FF14';
                const chartFont = '14px VT323';

                try {{ // Double Braces
                    function createCanvasIfMissing(containerId, canvasId) {{ // Double Braces
                        const container = document.getElementById(containerId);
                        if (!container) {{ console.error('Chart container missing:', containerId); return null; }} // Double Braces
                        let canvas = document.getElementById(canvasId);
                        if (!canvas) {{ // Double Braces
                            canvas = document.createElement('canvas'); canvas.id = canvasId;
                            container.innerHTML = ''; container.appendChild(canvas);
                            console.log('Created and appended canvas:', canvasId, 'to', containerId);
                        }} else {{ console.log('Found existing canvas:', canvasId); }} // Double Braces
                        canvas.width = container.clientWidth > 50 ? container.clientWidth : 300;
                        canvas.height = container.clientHeight > 50 ? container.clientHeight : 250;
                        if (canvas.width <= 0 || canvas.height <= 0) {{ // Double Braces
                            console.warn('Canvas has zero or negative dimensions:', canvasId, canvas.width, canvas.height);
                            canvas.width = 300; canvas.height = 250;
                        }} // Double Braces
                        return canvas;
                    }} // End Double Braces

                    function createPieChart(canvasId, data, colors) {{ // Double Braces
                        const canvas = document.getElementById(canvasId);
                        if (!canvas || !canvas.getContext) {{ console.error('PieChart: Canvas not ready:', canvasId); return; }} // Double Braces
                        const ctx = canvas.getContext('2d'); const width = canvas.width; const height = canvas.height;
                        ctx.clearRect(0, 0, width, height); const centerX = width / 2; const centerY = height / 2;
                        const radius = Math.min(centerX, centerY) * 0.65; let startAngle = -0.5 * Math.PI;
                        const total = data.reduce((sum, item) => sum + item.value, 0);
                        if (total === 0) {{ ctx.font = '18px VT323'; ctx.fillStyle = chartTextColor; ctx.textAlign = 'center'; ctx.fillText("No issue data", centerX, centerY); return; }} // Double Braces
                        data.forEach((item, i) => {{ if (item.value <= 0) return; const sliceAngle = 2 * Math.PI * item.value / total; const endAngle = startAngle + sliceAngle; ctx.beginPath(); ctx.moveTo(centerX, centerY); ctx.arc(centerX, centerY, radius, startAngle, endAngle); ctx.closePath(); ctx.fillStyle = colors[i % colors.length]; ctx.fill(); startAngle = endAngle; }}); // Double Braces forEach block
                        const legendFontSize = 14; const legendBoxSize = 12; const legendSpacing = 5; let legendX = 10; let legendY = 15;
                        ctx.font = legendFontSize + 'px VT323'; ctx.textAlign = 'left'; ctx.textBaseline = 'top';
                        data.forEach((item, i) => {{ ctx.fillStyle = colors[i % colors.length]; ctx.fillRect(legendX, legendY, legendBoxSize, legendBoxSize); ctx.fillStyle = chartTextColor; const labelText = `${{item.label}}: ${{item.value}} (${{(item.value / total * 100).toFixed(1)}}%)`; ctx.fillText(labelText, legendX + legendBoxSize + legendSpacing, legendY); legendY += legendFontSize + legendSpacing; if (legendY > height - legendFontSize) {{ legendY = 15; legendX += (ctx.measureText(labelText).width + 30); }} }}); // Double Braces forEach block and if block
                    }} // End Double Braces

                    function createBarChart(canvasId, data, title) {{ // Double Braces
                        const canvas = document.getElementById(canvasId);
                        if (!canvas || !canvas.getContext) {{ console.error('BarChart: Canvas not ready:', canvasId); return; }} // Double Braces
                        const ctx = canvas.getContext('2d'); const width = canvas.width; const height = canvas.height; ctx.clearRect(0, 0, width, height);
                        if (!data || data.length === 0) {{ ctx.font = '18px VT323'; ctx.fillStyle = chartTextColor; ctx.textAlign = 'center'; ctx.fillText("No data for " + title, width/2, height/2); return; }} // Double Braces
                        const marginTop = 40, marginRight = 20, marginBottom = 50, marginLeft = 50; const chartWidth = width - marginLeft - marginRight; const chartHeight = height - marginTop - marginBottom; if (chartWidth <= 0 || chartHeight <= 0) {{ console.warn("BarChart: Invalid dimensions:", chartWidth, chartHeight); return; }} // Double Braces
                        const barCount = data.length; const totalSpacing = chartWidth * 0.2; const barSpacing = totalSpacing / (barCount + 1); const barWidth = (chartWidth - totalSpacing) / barCount; const maxValue = Math.max(1, ...data.map(item => item.value));
                        ctx.strokeStyle = chartTextColor; ctx.lineWidth = 0.5; ctx.fillStyle = chartTextColor; ctx.font = '12px VT323'; ctx.textAlign = 'right'; ctx.textBaseline = 'middle'; const numYLabels = 5;
                        for(let i = 0; i <= numYLabels; i++) {{ const yPos = marginTop + chartHeight * (1 - i / numYLabels); const labelValue = (maxValue * i / numYLabels); const displayValue = labelValue >= 1 ? labelValue.toFixed(0) : labelValue.toFixed(1); ctx.fillText(displayValue, marginLeft - 8, yPos); ctx.beginPath(); ctx.moveTo(marginLeft - 4, yPos); ctx.lineTo(marginLeft + chartWidth, yPos); ctx.stroke(); }} // Double Braces for loop block
                        data.forEach((item, i) => {{ const barHeight = Math.max(1, (item.value / maxValue) * chartHeight); const x = marginLeft + barSpacing + (barWidth + barSpacing) * i; const y = marginTop + chartHeight - barHeight; ctx.fillStyle = chartAccent1; ctx.fillRect(x, y, barWidth, barHeight); const displayValue = item.origValue !== undefined ? item.origValue : item.value; ctx.fillStyle = chartTextColor; ctx.font = '12px VT323'; ctx.textAlign = 'center'; ctx.fillText(displayValue.toString(), x + barWidth / 2, y - 8); ctx.save(); ctx.translate(x + barWidth / 2, marginTop + chartHeight + 10); ctx.rotate(Math.PI / 6); ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText(item.label, 0, 0); ctx.restore(); }}); // Double Braces forEach block
                        ctx.strokeStyle = chartTextColor; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(marginLeft, marginTop); ctx.lineTo(marginLeft, marginTop + chartHeight); ctx.stroke(); ctx.beginPath(); ctx.moveTo(marginLeft, marginTop + chartHeight); ctx.lineTo(marginLeft + chartWidth, marginTop + chartHeight); ctx.stroke();
                        ctx.fillStyle = chartAccent2; ctx.font = '16px VT323'; ctx.textAlign = 'center'; ctx.fillText(title, width / 2, marginTop / 2);
                    }} // End Double Braces

                    // Data insertion remains the same - uses Python vars converted to JS strings
                    const pieData = {pie_data_js};
                    const langData = {lang_data_js};
                    const complexityData = {complexity_data_js};

                    // Create charts
                    const overallCanvas = createCanvasIfMissing('overallChart', 'overallCanvasElement');
                    const languageCanvas = createCanvasIfMissing('languageChart', 'languageCanvasElement');
                    const complexityCanvas = createCanvasIfMissing('complexityChart', 'complexityCanvasElement');

                    // Conditional execution needs no double braces
                    if (overallCanvas) createPieChart('overallCanvasElement', pieData, [chartHighlightColor, chartErrorColor, chartWarningColor, chartAccent2, chartAccent1]);
                    if (languageCanvas) createBarChart('languageCanvasElement', langData, 'Language Distribution');
                    if (complexityCanvas) createBarChart('complexityCanvasElement', complexityData, 'Code Quality Metrics');

                    console.log("Charts initialized.");

                }} catch (err) {{ console.error("Error executing chart JS:", err); }} // Double Braces try-catch
            }})(); // End IIFE - Double Braces
            """
            return js_code.strip()
        except Exception as e:
             self.update_progress(f"Error formatting chart JS data: {e}")
             return "// Error formatting chart JS data\n"


    def _generate_file_details_js(self, template_data):
        """Generate JavaScript for the file details pane, escaping braces for f-string."""
        try:
            # (Data extraction logic remains the same as v4.2)
            file_details_json = template_data.get('file_details_json', '{}')
            try: json.loads(file_details_json)
            except json.JSONDecodeError: file_details_json = '{}'
            pygments_available_js = 'true' if template_data.get('pygments_available') else 'false'

            # *** F-STRING WITH DOUBLED BRACES for JS code ***
            js_code = f"""
            // --- File Details JS ---
            (function() {{ // IIFE wrapper - Double Braces
                console.log("Initializing file details...");
                try {{ // Double Braces
                    // Data insertion remains the same
                    const fileDetailsData = {file_details_json};
                    const pygmentsAvailable = {pygments_available_js};

                    // Make function globally accessible
                    window.showFileDetails = function(displayPathKey) {{ // Double Braces for function body
                        console.log("Attempting showFileDetails for key:", displayPathKey);
                        const normalizedKey = displayPathKey.replace(/^\\/+|\\/+$/, '');
                        const fileData = fileDetailsData[normalizedKey];

                        const detailsDiv = document.getElementById('fileDetails');
                        const nameEl = document.getElementById('fileDetailsName');
                        const infoEl = document.getElementById('fileDetailsInfo');
                        const issuesEl = document.getElementById('fileDetailsIssues');
                        const codeEl = document.getElementById('fileDetailsCode');
                        const codePlaceholderEl = document.getElementById('fileDetailsCodePlaceholder');

                        if (!detailsDiv || !nameEl || !infoEl || !issuesEl) {{ console.error("Essential File detail elements missing!"); return; }} // Double Braces
                        if (pygmentsAvailable && !codeEl) {{ console.error("Pygments enabled, but code <pre> 'fileDetailsCode' missing!"); return; }} // Double Braces
                        if (!pygmentsAvailable && !codePlaceholderEl) {{ console.error("Pygments disabled, but placeholder <p> 'fileDetailsCodePlaceholder' missing!"); return; }} // Double Braces

                        if (!fileData) {{ // Double Braces
                            console.error(`File data not found for key: ${{displayPathKey}} (Normalized: ${{normalizedKey}}).`); // Python interpolation {{}} - OK
                            detailsDiv.style.display = 'block'; nameEl.textContent = 'Error';
                            infoEl.innerHTML = '<p class="error">Could not load details for this file path key.</p>';
                            issuesEl.innerHTML = '';
                            // Hide code elements if data not found
                            if (codeEl) codeEl.style.display = 'none';
                            if (codePlaceholderEl) codePlaceholderEl.style.display = 'none';
                            return;
                        }} // End Double Braces

                        console.log("File data found:", fileData.name);
                        detailsDiv.style.display = 'block';
                        nameEl.textContent = fileData.name || 'Unknown File';
                        // Using template literal for info - Python interpolation {{}} is OK here
                        infoEl.innerHTML = `
                            <p><span class="highlight">Path:</span> ${{normalizedKey}}</p>
                            <p><span class="highlight">Language:</span> ${{fileData.language || 'N/A'}}</p>
                            <p><span class="highlight">Lines:</span> ${{fileData.lines || 0}} total (${{fileData.code || 0}} code, ${{fileData.comments || 0}} comment, ${{fileData.blank || 0}} blank)</p>
                        `;

                        // --- Issues Display ---
                        let issuesHtml = '<h4>Issues Found:</h4>';
                        const all_issues_data = fileData.all_issues || {{}}; // Double braces for JS empty object
                        let totalFileIssues = 0;
                        // Double braces for JS object literal
                        const issueCategories = {{'code_smells': 'Smell', 'security_issues': 'Security', 'performance_issues': 'Perf.', 'style_issues': 'Style'}};
                        const severityOrder = {{ 'critical': 5, 'high': 4, 'medium': 3, 'low': 2, 'unknown': 1 }}; // Double braces for JS object literal
                        let issueListForDetails = [];

                        for (const categoryKey in issueCategories) {{ // Double Braces for loop block
                             if (all_issues_data.hasOwnProperty(categoryKey)) {{ // Double Braces for if block
                                 const issuesInCategory = all_issues_data[categoryKey] || [];
                                 totalFileIssues += issuesInCategory.length;
                                 // *** THIS IS THE LINE FROM THE ERROR ***
                                 // Double braces needed for forEach body and inner push object literal
                                 issuesInCategory.forEach(iss => {{ const severity = (iss.severity || 'unknown').toLowerCase(); issueListForDetails.push({{ line: iss.line || 'N/A', description: iss.description || 'No description.', context: iss.context || null, severity: severity, severityScore: severityOrder[severity] || 1, category_label: issueCategories[categoryKey] }}); }});
                             }} // End Double Braces for if block
                        }} // End Double Braces for loop block

                        if (totalFileIssues === 0) {{ issuesHtml += '<p>None detected in this file! Great job!</p>'; }} // Double Braces
                        else {{ // Double Braces for else block
                            issueListForDetails.sort((a, b) => {{ if (b.severityScore !== a.severityScore) return b.severityScore - a.severityScore; const lineA = parseInt(a.line, 10) || Infinity; const lineB = parseInt(b.line, 10) || Infinity; return lineA - lineB; }}); // Double braces for sort function body
                            issuesHtml += `<ul style="font-size: 14px; max-height: 200px; overflow-y: auto; list-style-type: none; padding-left: 0;">`;
                            // Double braces for forEach body and Python interpolation {{}} inside JS template literal `${{...}}`
                            issueListForDetails.forEach(issue => {{ const desc = issue.description.replace(/</g, "<").replace(/>/g, ">"); issuesHtml += `<li style="margin-bottom: 8px; border-bottom: 1px dashed rgba(0,255,0,0.2); padding-bottom: 5px;"><span class="severity-badge severity-${{issue.severity}}">${{issue.severity}}</span> <strong>${{issue.category_label}}</strong> (Line ${{issue.line}}): ${{desc}}</li>`; }});
                            issuesHtml += '</ul>';
                         }} // End Double Braces for else block
                        issuesEl.innerHTML = issuesHtml;


                        // --- Code Display ---
                        if (pygmentsAvailable && codeEl) {{ // Double Braces
                           codeEl.innerHTML = '<p style="font-size: 14px; font-style: italic;">(Syntax highlighting rendered by backend)</p>';
                           codeEl.style.display = 'block'; if (codePlaceholderEl) codePlaceholderEl.style.display = 'none';
                        }} else if (codePlaceholderEl) {{ // Double Braces
                           codePlaceholderEl.textContent = 'Syntax highlighting not available (Pygments package missing or disabled).';
                           codePlaceholderEl.style.display = 'block'; if (codeEl) codeEl.style.display = 'none';
                        }} // End Double Braces

                    }}; // End Double Braces for function body
                    console.log("File details function defined and attached to window.");

                }} catch (err) {{ // Double Braces for catch block
                    console.error("Error setting up file details JS:", err);
                    const detailsDiv = document.getElementById('fileDetails');
                    if(detailsDiv) {{ detailsDiv.style.display = 'block'; detailsDiv.innerHTML = '<h3 style="color:var(--error-color);">Error</h3><p class="error">Failed to initialize file browser JavaScript. Check console.</p>'; }} // Double Braces for if block
                }} // End Double Braces for catch block
            }})(); // End IIFE - Double Braces
            """
            return js_code.strip()
        except Exception as e:
             self.update_progress(f"Error formatting file details JS: {e}")
             return "// Error formatting file details JS\n"


    def _generate_graph_js(self, template_data):
        """Generate JavaScript for the vis.js graph, escaping braces for f-string."""
        try:
            # (Data extraction logic remains the same as v4.2)
            graph_data = template_data.get('dependency_graph')
            if graph_data and isinstance(graph_data, dict) and isinstance(graph_data.get('nodes'), list) and graph_data['nodes']:
                 valid_nodes = [n for n in graph_data['nodes'] if isinstance(n, dict)]
                 valid_edges = [e for e in graph_data['edges'] if isinstance(e, dict)]
                 if not valid_nodes:
                     self.update_progress("DEBUG: Graph data present but contains no valid nodes, skipping graph JS.")
                     return self._get_no_graph_js("No internal dependency nodes found.") # Use helper (already handles braces correctly)

                 valid_nodes_str = json.dumps(valid_nodes)
                 valid_edges_str = json.dumps(valid_edges)

                 # *** F-STRING WITH DOUBLED BRACES for JS code ***
                 graph_js = f"""
                // --- Dependency Graph JS ---
                (function() {{ // IIFE Wrapper - Double Braces
                    console.log("Initializing dependency graph...");
                    const graphContainer = document.getElementById('dependencyGraphContainer');
                    const loadingMsg = document.getElementById('graphLoadingMsg');
                    const errorMsgDiv = document.getElementById('graphErrorMsg');

                    if (!graphContainer) {{ console.error("Graph container 'dependencyGraphContainer' not found."); return; }} // Double Braces
                    if (!errorMsgDiv) {{ console.warn("Graph error message div 'graphErrorMsg' not found."); }} // Double Braces
                    if (loadingMsg) {{ loadingMsg.style.display = 'block'; loadingMsg.textContent = 'Loading graph...'; }} // Double Braces
                    if (errorMsgDiv) {{ errorMsgDiv.style.display = 'none'; }} // Double Braces

                    if (typeof vis === 'undefined' || typeof vis.Network === 'undefined') {{ // Double Braces
                        console.error('vis.js library not loaded!');
                        if (loadingMsg) loadingMsg.style.display = 'none';
                        if (errorMsgDiv) {{ errorMsgDiv.textContent = 'Error: vis.js library failed to load. Cannot display graph.'; errorMsgDiv.style.display = 'block'; }} // Double Braces
                        return;
                    }} // End Double Braces

                    try {{ // Double Braces for try block
                        console.log("Graph container found, vis.js loaded.");
                        // Data insertion OK - uses Python vars
                        const nodeData = {valid_nodes_str};
                        const edgeData = {valid_edges_str};
                        console.log(`Graph Data: ${{nodeData.length}} nodes, ${{edgeData.length}} edges.`); // Python interpolation {{}} OK

                        const nodes = new vis.DataSet(nodeData);
                        const edges = new vis.DataSet(edgeData);
                        // Double braces for JS object literal
                        const data = {{ nodes: nodes, edges: edges }};

                        // Get colors (OK - uses JS functions)
                        const nodeBgColor = getComputedStyle(document.documentElement).getPropertyValue('--code-bg') || 'rgba(0, 50, 0, 0.7)';
                        const nodeBorderColor = getComputedStyle(document.documentElement).getPropertyValue('--accent1-color') || '#00FFFF';
                        const nodeHighlightBg = getComputedStyle(document.documentElement).getPropertyValue('--card-bg') || 'rgba(0, 255, 0, 0.1)';
                        const nodeHighlightBorder = getComputedStyle(document.documentElement).getPropertyValue('--highlight-color') || '#39FF14';
                        const edgeColor = getComputedStyle(document.documentElement).getPropertyValue('--accent2-color') || '#FF00FF';
                        const textColor = getComputedStyle(document.documentElement).getPropertyValue('--text-color') || '#00FF00';

                        // Double braces needed for the main options object literal and all nested object literals
                        const options = {{
                            nodes: {{
                                shape: 'box',
                                font: {{ color: textColor, face: 'VT323', size: 16 }}, // Nested object {{}}
                                color: {{ // Nested object {{}}
                                     background: nodeBgColor, border: nodeBorderColor,
                                     highlight: {{ background: nodeHighlightBg, border: nodeHighlightBorder }}, // Nested object {{}}
                                     hover: {{ background: nodeHighlightBg, border: nodeHighlightBorder }} // Nested object {{}}
                                }},
                                margin: 12,
                                widthConstraint: {{ minimum: 80, maximum: 300 }}, // Nested object {{}}
                                borderWidth: 1.5
                            }},
                            edges: {{ // Nested object {{}}
                                arrows: {{ to: {{ enabled: true, scaleFactor: 0.8, type: 'arrow' }} }}, // Nested object {{}}
                                color: {{ color: edgeColor, highlight: nodeHighlightBorder, hover: nodeHighlightBorder, opacity: 0.8 }}, // Nested object {{}}
                                width: 1.5,
                                hoverWidth: 2.5,
                                smooth: {{ // Nested object {{}}
                                    enabled: true,
                                    type: 'cubicBezier',
                                    forceDirection: 'vertical',
                                    roundness: 0.6
                                }}
                            }},
                            layout: {{ // Nested object {{}}
                                hierarchical: {{ // Nested object {{}}
                                     enabled: true,
                                     direction: 'UD',
                                     sortMethod: 'directed',
                                     levelSeparation: 150,
                                     nodeSpacing: 150,
                                     treeSpacing: 200
                                }}
                            }},
                            physics: {{ enabled: false }}, // Nested object {{}}
                            interaction: {{ // Nested object {{}}
                                dragNodes: true, dragView: true, zoomView: true,
                                hover: true, tooltipDelay: 200,
                                navigationButtons: true,
                                keyboard: true
                            }}
                        }}; // End options object {{}}

                        // Create the network
                        const network = new vis.Network(graphContainer, data, options);

                        // Double braces for function bodies
                        network.on("stabilizationProgress", function(params) {{
                            const progress = Math.round(params.iterations / params.total * 100);
                             if (loadingMsg) loadingMsg.textContent = `Rendering graph: ${{progress}}%`; // Python interpolation {{}} OK
                        }});
                        network.once("stabilizationIterationsDone", function() {{ // Double braces
                            if (loadingMsg) loadingMsg.style.display = 'none';
                            console.log("Vis.js network stabilization complete.");
                        }});
                         network.on("showPopup", function (nodeId) {{ // Double braces
                            const node = nodes.get(nodeId);
                            const msgDiv = document.getElementById('graphLoadingMsg'); // Use loadingMsg div for simplicity
                            if(node && node.title && msgDiv) {{ // Double braces for if block
                                msgDiv.innerHTML = node.title; // Use innerHTML if title contains HTML
                                msgDiv.style.display = 'block';
                            }} // End Double Braces
                          }});
                          network.on("hidePopup", function () {{ // Double braces
                             const msgDiv = document.getElementById('graphLoadingMsg');
                             if(msgDiv) msgDiv.style.display = 'none';
                          }});


                        // Double braces for resize function body
                        const resizeObserver = new ResizeObserver(() => {{
                            network.fit({{ animation: false }}); // Double braces for object literal
                        }});
                        resizeObserver.observe(graphContainer);

                        console.log("Vis.js network initialized and listeners added.");

                     }} catch (err) {{ // Double braces for catch block
                         console.error("Vis.js rendering error:", err);
                         if (loadingMsg) loadingMsg.style.display = 'none';
                         if (errorMsgDiv) {{ // Double braces for if block
                            errorMsgDiv.textContent = 'Error rendering dependency graph: ' + err.message;
                            errorMsgDiv.style.display = 'block';
                         }} // End Double Braces
                     }} // End Double Braces
                }})(); // End IIFE - Double Braces
                """
                 return graph_js.strip()
            else:
                 self.update_progress("DEBUG: No valid graph data found, skipping graph JS generation.")
                 # _get_no_graph_js handles its own braces correctly
                 return self._get_no_graph_js("No internal dependencies found or data unavailable.")
        except Exception as e:
             self.update_progress(f"Error formatting graph JS data: {e}")
             # _get_no_graph_js handles its own braces correctly
             error_msg = f"Error preparing graph JS: {str(e)}".replace("'", "\\'")
             return self._get_no_graph_js(error_msg, is_error=True)


    # --- _get_no_graph_js method ---
    # (Keep the previously corrected _get_no_graph_js method from v4.2 - it was correct)
    def _get_no_graph_js(self, message, is_error=False):
        """Helper to generate JS for when no graph is displayed."""
        message_escaped = message.replace("'", "\\'")
        # This f-string *only* uses Python interpolation, so no double braces needed here
        js = f"""
        // --- Graph JS Placeholder ---
        (function() {{
            const graphContainer = document.getElementById('dependencyGraphContainer');
            const loadingMsg = document.getElementById('graphLoadingMsg');
            const errorMsgDiv = document.getElementById('graphErrorMsg');
            if (loadingMsg) {{ loadingMsg.style.display = 'none'; }}
            const displayDiv = {'errorMsgDiv' if is_error else 'loadingMsg'};
            if (displayDiv) {{
                displayDiv.textContent = '{message_escaped}';
                displayDiv.style.display = 'block';
                if({is_error} && errorMsgDiv) {{ errorMsgDiv.className = 'error-box'; errorMsgDiv.style.position='relative'; errorMsgDiv.style.top=''; errorMsgDiv.style.left=''; errorMsgDiv.style.transform=''; }}
                if(graphContainer) {{ graphContainer.style.height = '80px'; }}
            }} else {{ console.warn("Could not find graph message element to update: {message_escaped}"); }}
        }})();
        """
        return js.strip()

    # --- generate_text_report method ---
    # (Keep the previously corrected generate_text_report method from v4.2)
    def generate_text_report(self, basic_analysis, advanced_analysis):
        self.update_progress("DEBUG: Text report generation not fully implemented.")
        report_lines = ["Rick's Basic Text Analysis\n", "="*30 + "\n"]
        if basic_analysis:
            report_lines.append(f"Project: {basic_analysis.get('project_path', 'N/A')}")
            # ... add more details ...
        if advanced_analysis:
             report_lines.append("\n" + "="*30 + "\nAdvanced Summary:\n" + "="*30 + "\n")
             # ... add details ...
        return "\n".join(report_lines)


# Standalone testing block (optional)
if __name__ == "__main__":
    print("Advanced Reporter module loaded (v4.3 - Fixed f-string JS brace errors).")