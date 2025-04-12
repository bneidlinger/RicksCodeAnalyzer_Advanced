#!/usr/bin/env python3
# Advanced Code Analyzer Module for Rick's Code Analyzer
# This module provides advanced code analysis capabilities

import os
import re
import ast
import json
import datetime
import time
from collections import defaultdict, Counter
import chardet

# List of common code smells and anti-patterns to detect
CODE_SMELLS = {
    'long_function': {
        'description': 'Functions that are too long (over 50 lines)',
        'severity': 'medium',
        'language': 'all'
    },
    'too_many_parameters': {
        'description': 'Functions with too many parameters (over 5)',
        'severity': 'medium',
        'language': 'all'
    },
    'complex_conditional': {
        'description': 'Overly complex conditional expressions',
        'severity': 'medium',
        'language': 'all'
    },
    'deep_nesting': {
        'description': 'Deeply nested code blocks (over 4 levels)',
        'severity': 'high',
        'language': 'all'
    },
    'duplicate_code': {
        'description': 'Duplicate or very similar code blocks',
        'severity': 'high',
        'language': 'all'
    },
    'magic_number': {
        'description': 'Magic numbers (hard-coded numeric literals)',
        'severity': 'low',
        'language': 'all'
    },
    'commented_code': {
        'description': 'Commented-out code blocks',
        'severity': 'low',
        'language': 'all'
    },
    'global_variable': {
        'description': 'Excessive use of global variables',
        'severity': 'medium',
        'language': 'all'
    },
    'long_line': {
        'description': 'Lines that are too long (over 100 characters)',
        'severity': 'low',
        'language': 'all'
    },
    'empty_catch': {
        'description': 'Empty catch blocks',
        'severity': 'medium',
        'language': 'all'
    }
}

# Python-specific anti-patterns
PYTHON_ANTI_PATTERNS = {
    'bare_except': {
        'description': 'Using bare except: statements',
        'severity': 'high',
        'regex': r'except\s*:'
    },
    'import_star': {
        'description': 'Using from module import *',
        'severity': 'medium',
        'regex': r'from\s+\w+\s+import\s+\*'
    },
    'mutable_default': {
        'description': 'Using mutable default arguments',
        'severity': 'medium',
        'regex': r'def\s+\w+\s*\([^)]*=\s*(\[\]|\{\}|\(\))'
    },
    'eval_usage': {
        'description': 'Using eval() function',
        'severity': 'high',
        'regex': r'eval\s*\('
    }
}

# JavaScript-specific anti-patterns
JS_ANTI_PATTERNS = {
    'var_usage': {
        'description': 'Using var instead of let/const',
        'severity': 'medium',
        'regex': r'\bvar\s+'
    },
    'triple_equals': {
        'description': 'Using == instead of ===',
        'severity': 'medium',
        'regex': r'[^=!]==[^=]'
    },
    'eval_usage': {
        'description': 'Using eval() function',
        'severity': 'high',
        'regex': r'eval\s*\('
    },
    'with_statement': {
        'description': 'Using with statement',
        'severity': 'high',
        'regex': r'\bwith\s*\('
    }
}

# Common security vulnerabilities to detect
SECURITY_VULNERABILITIES = {
    'sql_injection': {
        'description': 'Potential SQL Injection vulnerabilities',
        'severity': 'critical',
        'regex': r'.*(?:execute|query|run).*\+.*|.*(?:execute|query|run).*\$\{',
        'languages': ['python', 'javascript', 'php', 'ruby']
    },
    'xss': {
        'description': 'Potential Cross-Site Scripting (XSS) vulnerabilities',
        'severity': 'critical',
        'regex': r'innerHTML\s*=|document\.write\s*\(',
        'languages': ['javascript', 'html']
    },
    'eval_input': {
        'description': 'Evaluating user input (can lead to code injection)',
        'severity': 'critical',
        'regex': r'eval\s*\(.*(?:input|param|request|query|\$_GET|\$_POST)',
        'languages': ['python', 'javascript', 'php']
    },
    'hardcoded_credentials': {
        'description': 'Hardcoded credentials or API keys',
        'severity': 'critical',
        'regex': r'password\s*=\s*["\'][^"\']+["\']|api[_-]?key\s*=\s*["\'][^"\']+["\']',
        'languages': ['all']
    }
}

# Common performance issues to detect
PERFORMANCE_ISSUES = {
    'inefficient_loop': {
        'description': 'Inefficient loop patterns',
        'severity': 'medium',
        'regex': r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\(\s*\w+\s*\)\s*\)',
        'languages': ['python']
    },
    'nested_loops': {
        'description': 'Nested loops with high complexity',
        'severity': 'high',
        'languages': ['all']
    },
    'multiple_dom_access': {
        'description': 'Multiple DOM accesses that could be cached',
        'severity': 'medium',
        'regex': r'document\.getElement(s)?By|\$\(\s*[\'"]',
        'languages': ['javascript']
    }
}

# Best practices for each language
BEST_PRACTICES = {
    'python': [
        'Use list comprehensions instead of map/filter when possible',
        'Follow PEP 8 style guide',
        'Use context managers (with statements) for file operations',
        'Prefer f-strings for string formatting in Python 3.6+',
        'Use virtual environments for project dependencies',
        'Use type hints for better code readability and tool support'
    ],
    'javascript': [
        'Use const and let instead of var',
        'Use === instead of ==',
        'Use promises or async/await for asynchronous operations',
        'Use destructuring for cleaner code',
        'Use template literals instead of string concatenation',
        'Use ESLint to enforce code style'
    ],
    'java': [
        'Follow the Java naming conventions',
        'Use try-with-resources for resource management',
        'Prefer StringBuilder over String concatenation in loops',
        'Use the @Override annotation when overriding methods',
        'Use generics for type safety'
    ]
}


class AdvancedCodeAnalyzer:
    """Advanced code analysis capabilities for Rick's Code Analyzer"""

    def __init__(self, callback_function=None):
        """Initialize the analyzer

        Args:
            callback_function: Function to call for progress updates
        """
        self.results = {
            'code_smells': defaultdict(list),
            'security_issues': defaultdict(list),
            'performance_issues': defaultdict(list),
            'style_issues': defaultdict(list),
            'complexity_metrics': {},
            'dependencies': defaultdict(set),
            'token_stats': defaultdict(int),
            'duplicated_code': [],
            'best_practices': {}
        }

        self.callback = callback_function
        self.duplicated_blocks = defaultdict(list)
        self.file_metrics = {}
        self.analyzed_files = set()
        self.function_metrics = defaultdict(dict)
        self.import_graph = defaultdict(set)

    def update_progress(self, message):
        """Update progress via callback"""
        if self.callback:
            self.callback(message)
        else:
            print(message)

    def analyze_project(self, project_path, file_stats):
        """Run advanced analysis on the project

        Args:
            project_path: Path to the project directory
            file_stats: Dictionary of file statistics from basic analysis

        Returns:
            Dictionary containing analysis results
        """
        start_time = time.time()
        self.update_progress("Starting advanced analysis...")

        # Extract list of files
        files_to_analyze = [file_data['path'] for file_data in file_stats.values()]
        self.analyzed_files = set(files_to_analyze)

        # Analyze each file
        for file_path in files_to_analyze:
            ext = os.path.splitext(file_path)[1].lower()
            language = self._get_language_from_extension(ext)

            if language != "Unknown":
                self.update_progress(f"Analyzing {os.path.basename(file_path)}...")

                try:
                    with open(file_path, 'rb') as f:
                        raw_content = f.read()

                    # Detect encoding
                    result = chardet.detect(raw_content)
                    encoding = result['encoding'] if result['encoding'] else 'utf-8'

                    # Decode content with detected encoding
                    try:
                        content = raw_content.decode(encoding, errors='replace')
                    except UnicodeDecodeError:
                        # Fallback to utf-8 with more error handling
                        content = raw_content.decode('utf-8', errors='replace')

                    # Language-specific analysis
                    if language == "Python":
                        self._analyze_python_file(file_path, content)
                    elif language in ["JavaScript", "TypeScript"]:
                        self._analyze_js_file(file_path, content)

                    # Generic analysis for all languages
                    self._analyze_generic(file_path, content, language)

                    # Check for duplicated code blocks
                    self._check_duplicated_code(file_path, content, language)

                except Exception as e:
                    self.update_progress(f"Error analyzing {file_path}: {str(e)}")

        # Post-processing analysis
        self._analyze_dependencies()
        self._analyze_duplicated_code()
        self._identify_best_practices()

        # Calculate complexity metrics for the whole project
        self._calculate_project_metrics()

        analysis_time = time.time() - start_time
        self.results['analysis_metadata'] = {
            'timestamp': datetime.datetime.now().isoformat(),
            'duration_seconds': round(analysis_time, 2),
            'files_analyzed': len(self.analyzed_files)
        }

        self.results['import_graph'] = self.import_graph  # Ensure the graph is in the results

        self.update_progress(f"Advanced analysis completed in {analysis_time:.2f} seconds")
        return self.results

    def _get_language_from_extension(self, extension):
        """Get programming language from file extension"""
        languages = {
            '.py': 'Python',
            '.pyw': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.c': 'C',
            '.cpp': 'C++',
            '.h': 'C/C++',
            '.hpp': 'C++',
            '.cs': 'C#',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.go': 'Go',
            '.rs': 'Rust',
            '.html': 'HTML',
            '.htm': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'SASS',
            '.less': 'LESS',
            '.sql': 'SQL'
        }
        return languages.get(extension, "Unknown")

    def _analyze_python_file(self, file_path, content):
        """Analyze Python file using AST, with better error handling"""
        try:
            tree = ast.parse(content, filename=file_path)
            # Run sub-analyses WITHIN the try block
            self._analyze_python_imports(tree, file_path)
            self._analyze_python_functions(tree, file_path) # This might raise AttributeError
            # Apply specific regex patterns even if AST works (optional but safe)
            self._apply_regex_patterns(PYTHON_ANTI_PATTERNS, file_path, content, 'code_smells')
            return True # Indicate successful AST processing

        except SyntaxError as e:
            self.update_progress(f"Syntax error in {os.path.basename(file_path)} (line {e.lineno}): {e.msg}. Using regex fallback.")
            self.results['style_issues'][file_path].append({'type': 'syntax_error','description': f'Python syntax error prevents AST analysis (line {e.lineno}: {e.msg})','severity': 'warning','line': e.lineno})
            self._analyze_python_with_regex(file_path, content) # Run full regex fallback
            return False # Indicate parse failure

        except AttributeError as ae:
             # Specific catch for AttributeError, likely from ast.unparse or similar
             self.update_progress(f"AST analysis feature error in {os.path.basename(file_path)} ({ae}). Using regex fallback.")
             self.results['style_issues'][file_path].append({'type': 'ast_feature_error','description': f'AST analysis failed ({ae}). Analysis may be incomplete.','severity': 'warning','line': 1})
             self._analyze_python_with_regex(file_path, content) # Run full regex fallback
             return False # Indicate parse failure

        except Exception as e:
             # Catch any other unexpected errors during AST processing
             self.update_progress(f"Unexpected error during AST processing for {os.path.basename(file_path)}: {type(e).__name__}. Using regex fallback.")
             # Optional: Add traceback for debugging
             # import traceback
             # self.update_progress(traceback.format_exc())
             self.results['style_issues'][file_path].append({'type': 'ast_processing_error','description': f'Unexpected AST processing error: {type(e).__name__}.','severity': 'error','line': 1})
             self._analyze_python_with_regex(file_path, content) # Run full regex fallback
             return False

    def _analyze_python_imports(self, tree, file_path):
        """Analyze Python imports from AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    self.import_graph[file_path].add(name.name)
                    self.results['dependencies'][file_path].add(name.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module
                    self.import_graph[file_path].add(module_name)
                    self.results['dependencies'][file_path].add(module_name)

    def _analyze_python_functions(self, tree, file_path):
        """Analyze Python functions from AST, calculating size robustly"""
        # self.function_metrics[file_path] = {} # Clear/init metrics for this file

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                line_num = node.lineno

                # Count parameters (original logic seems fine)
                params_count = len(node.args.args) # Simplified, add kwonlyargs etc. if needed from original
                # ... add back original robust param counting if needed ...
                params_count = len(node.args.args) + len(node.args.posonlyargs) + len(node.args.kwonlyargs)
                if node.args.vararg: params_count += 1
                if node.args.kwarg: params_count += 1


                # --- Robust Line Count ---
                lines_of_code = 1 # Default
                try:
                    # Prefer end_lineno if available (Python 3.8+)
                    start_line = getattr(node, 'lineno', 0)
                    end_line = getattr(node, 'end_lineno', 0)
                    if start_line and end_line:
                         lines_of_code = (end_line - start_line) + 1
                    else:
                        # Fallback: Estimate based on body size if unparse fails or unavailable
                         lines_of_code = len(node.body) + 2 # Rough estimate
                         # Try unparse only if needed and available
                         if hasattr(ast, 'unparse'):
                             try:
                                 lines_of_code = len(ast.unparse(node).split('\n'))
                             except Exception:
                                 pass # Stick with body estimate if unparse fails
                except Exception:
                     lines_of_code = 10 # Final fallback guess

                # --- Report smells ---
                if params_count > 5:
                    self.results['code_smells'][file_path].append({'type': 'too_many_parameters','description': f"Function '{func_name}' has {params_count} parameters",'severity': 'medium','line': line_num})
                if lines_of_code > 50:
                    self.results['code_smells'][file_path].append({'type': 'long_function','description': f"Function '{func_name}' is approx. {lines_of_code} lines long",'severity': 'medium','line': line_num})

                # --- Complexity (Keep original simplified logic) ---
                complexity = 1
                for inner_node in ast.walk(node):
                    if isinstance(inner_node, (ast.If, ast.While, ast.For, ast.Try, ast.AsyncFor)): complexity += 1
                    elif isinstance(inner_node, ast.BoolOp) and isinstance(inner_node.op, ast.And): complexity += len(inner_node.values) - 1
                # Report high complexity if desired (add check here)
                if complexity > 10:
                     self.results['code_smells'][file_path].append({'type': 'high_complexity','description': f"Function '{func_name}' has high cyclomatic complexity ({complexity})",'severity': 'medium','line': line_num})


                # --- Store metrics ---
                func_key = f"{func_name}@{line_num}"
                self.function_metrics[file_path][func_key] = {
                    'name': func_name,
                    'params': params_count,
                    'lines': lines_of_code,
                    'complexity': complexity,
                    'line': line_num
                }

                # --- Nesting check ---
                self._check_python_nesting(node, func_name, file_path) # Keep original call signature

    def _apply_regex_patterns(self, patterns_dict, file_path, content, result_category):
        """Applies a dictionary of regex patterns to content and stores results."""
        lines = None
        for pattern_name, pattern_data in patterns_dict.items():
            try:
                for match in re.finditer(pattern_data['regex'], content):
                    line_num = content.count('\n', 0, match.start()) + 1
                    if lines is None: lines = content.split('\n')
                    context_line = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                    self.results[result_category][file_path].append(
                        {'type': pattern_name, 'description': pattern_data['description'],
                         'severity': pattern_data['severity'], 'line': line_num, 'context': context_line})
            except Exception as regex_err:
                self.update_progress(f"Regex error for '{pattern_name}' in {os.path.basename(file_path)}: {regex_err}")

    def _check_python_nesting(self, node, func_name, file_path, current_depth=0):
        """Check for deep nesting in Python code"""
        # Increment depth for control structures
        if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.AsyncFor, ast.AsyncWith)):
            current_depth += 1

            # Report deep nesting
            if current_depth > 4:
                self.results['code_smells'][file_path].append({
                    'type': 'deep_nesting',
                    'description': f"Deep nesting (level {current_depth}) in function '{func_name}'",
                    'severity': 'high',
                    'line': node.lineno
                })

        # Recurse through all child nodes
        for child in ast.iter_child_nodes(node):
            self._check_python_nesting(child, func_name, file_path, current_depth)

    def _analyze_python_with_regex(self, file_path, content):
        """Analyze Python file using regex patterns when AST parsing fails"""
        # Check for Python-specific anti-patterns
        for pattern_name, pattern_data in PYTHON_ANTI_PATTERNS.items():
            matches = re.finditer(pattern_data['regex'], content)
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                self.results['code_smells'][file_path].append({
                    'type': pattern_name,
                    'description': pattern_data['description'],
                    'severity': pattern_data['severity'],
                    'line': line_number
                })

        # Estimate dependencies
        import_matches = re.finditer(r'(?:from|import)\s+([\w\.]+)', content)
        for match in import_matches:
            dependency = match.group(1).split(' as ')[0].strip()
            if dependency:
                self.results['dependencies'][file_path].add(dependency)

    def _analyze_js_file(self, file_path, content):
        """Analyze JavaScript file"""
        # Check for JS-specific anti-patterns
        for pattern_name, pattern_data in JS_ANTI_PATTERNS.items():
            matches = re.finditer(pattern_data['regex'], content)
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                self.results['code_smells'][file_path].append({
                    'type': pattern_name,
                    'description': pattern_data['description'],
                    'severity': pattern_data['severity'],
                    'line': line_number
                })

        # Estimate dependencies (imports/requires)
        # ES6 imports
        import_matches = re.finditer(r'import\s+.*from\s+[\'"]([^\'"]+)[\'"]', content)
        for match in import_matches:
            self.results['dependencies'][file_path].add(match.group(1))

        # CommonJS requires
        require_matches = re.finditer(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content)
        for match in require_matches:
            self.results['dependencies'][file_path].add(match.group(1))

        # Find functions (simplified approach)
        func_matches = re.finditer(
            r'(?:function\s+(\w+)|(\w+)\s*=\s*function|const\s+(\w+)\s*=\s*(?:\(.*\)|async\s*(?:\(.*\))))', content)
        for match in matches:
            func_name = match.group(1) or match.group(2) or match.group(3)
            if func_name:
                line_number = content[:match.start()].count('\n') + 1

                # Check for long functions (simplified)
                func_start = match.start()
                opening_braces = 1
                closing_braces = 0

                for i in range(func_start + match.group(0).index('{') + 1, len(content)):
                    if content[i] == '{':
                        opening_braces += 1
                    elif content[i] == '}':
                        closing_braces += 1

                    if opening_braces == closing_braces:
                        func_end = i
                        break

                func_content = content[func_start:func_end]
                lines_of_code = func_content.count('\n')

                if lines_of_code > 50:
                    self.results['code_smells'][file_path].append({
                        'type': 'long_function',
                        'description': f"Function '{func_name}' is {lines_of_code} lines long",
                        'severity': 'medium',
                        'line': line_number
                    })

    def _analyze_generic(self, file_path, content, language):
        """Generic analysis applicable to all languages"""
        lines = content.split('\n')

        # Check for long lines
        for i, line in enumerate(lines):
            if len(line.strip()) > 100:
                self.results['style_issues'][file_path].append({
                    'type': 'long_line',
                    'description': 'Line exceeds 100 characters',
                    'line': i + 1,
                    'severity': 'low'
                })

        # Check for commented code
        comment_markers = {
            'Python': ['#'],
            'JavaScript': ['//', '/*'],
            'Java': ['//', '/*'],
            'C': ['//', '/*'],
            'C++': ['//', '/*'],
            'C#': ['//', '/*'],
            'Ruby': ['#'],
            'PHP': ['//', '/*', '#'],
            'Swift': ['//', '/*'],
            'Go': ['//'],
            'Rust': ['//', '/*'],
        }

        markers = comment_markers.get(language, ['#', '//'])
        in_block_comment = False
        commented_code_lines = []
        current_block = []

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                continue

            # Check for block comments start/end
            if language in ['JavaScript', 'Java', 'C', 'C++', 'C#', 'PHP', 'Swift']:
                if '/*' in line_stripped and '*/' not in line_stripped[line_stripped.index('/*') + 2:]:
                    in_block_comment = True

                if '*/' in line_stripped and in_block_comment:
                    in_block_comment = False

            # Check if line is a comment
            is_comment = False
            for marker in markers:
                if line_stripped.startswith(marker):
                    is_comment = True
                    break

            if is_comment or in_block_comment:
                # Check if comment line contains code
                code_indicators = [
                    r'\bif\b', r'\bfor\b', r'\bwhile\b', r'\bdef\b', r'\bfunction\b',
                    r'\breturn\b', r'\bclass\b', r'{', r'}', r'=', r'\(.*\)'
                ]

                for indicator in code_indicators:
                    # Remove the comment marker before checking
                    code_line = line_stripped
                    for marker in markers:
                        if code_line.startswith(marker):
                            code_line = code_line[len(marker):].strip()
                            break

                    if re.search(indicator, code_line):
                        current_block.append((i + 1, line_stripped))
                        break
            else:
                # If we have collected commented code and now found non-comment line
                if current_block:
                    if len(current_block) > 1:  # Only consider blocks of 2+ lines
                        commented_code_lines.append(current_block)
                    current_block = []

        # Add remaining block if any
        if current_block and len(current_block) > 1:
            commented_code_lines.append(current_block)

        # Report commented code blocks
        for block in commented_code_lines:
            start_line = block[0][0]
            end_line = block[-1][0]
            self.results['code_smells'][file_path].append({
                'type': 'commented_code',
                'description': f"Commented-out code block (lines {start_line}-{end_line})",
                'severity': 'low',
                'line': start_line
            })

        # Check for security vulnerabilities
        for vuln_name, vuln_data in SECURITY_VULNERABILITIES.items():
            # Skip if vulnerability not applicable to this language
            if 'languages' in vuln_data and 'all' not in vuln_data['languages']:
                if language.lower() not in [lang.lower() for lang in vuln_data['languages']]:
                    continue

            # Check for vulnerability pattern
            matches = re.finditer(vuln_data['regex'], content)
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                self.results['security_issues'][file_path].append({
                    'type': vuln_name,
                    'description': vuln_data['description'],
                    'severity': vuln_data['severity'],
                    'line': line_number,
                    'context': content.split('\n')[line_number - 1].strip()
                })

        # Check for performance issues
        for issue_name, issue_data in PERFORMANCE_ISSUES.items():
            # Skip if not applicable to this language
            if 'languages' in issue_data and 'all' not in issue_data['languages']:
                if language.lower() not in [lang.lower() for lang in issue_data['languages']]:
                    continue

            # If regex is available, use it
            if 'regex' in issue_data:
                matches = re.finditer(issue_data['regex'], content)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    self.results['performance_issues'][file_path].append({
                        'type': issue_name,
                        'description': issue_data['description'],
                        'severity': issue_data['severity'],
                        'line': line_number,
                        'context': content.split('\n')[line_number - 1].strip()
                    })

        # Check for nested loops (general performance issue)
        if issue_name == 'nested_loops':
            # Different loop patterns for different languages
            loop_patterns = {
                'Python': r'\b(for|while)\b',
                'JavaScript': r'\b(for|while|do)\b',
                'Java': r'\b(for|while|do)\b',
                'C': r'\b(for|while|do)\b',
                'C++': r'\b(for|while|do)\b',
                'C#': r'\b(for|while|do|foreach)\b',
                'Ruby': r'\b(for|while|until|each)\b',
                'PHP': r'\b(for|while|do|foreach)\b'
            }

            loop_regex = loop_patterns.get(language, r'\b(for|while)\b')
            loop_matches = list(re.finditer(loop_regex, content))

            # Check for nesting
            for i, match in enumerate(loop_matches):
                loop_start = match.start()
                line_number = content[:loop_start].count('\n') + 1

                # Find the block for this loop
                # (Simplified approach - won't work for all cases)
                opening_bracket = content.find('{', loop_start)
                if opening_bracket == -1:  # Python or other language without braces
                    opening_bracket = content.find(':', loop_start)
                    if opening_bracket == -1:
                        continue

                    # For Python, find the indented block
                    next_line_start = content.find('\n', opening_bracket) + 1
                    if next_line_start >= len(content):
                        continue

                    # Find the indentation level
                    next_line_end = content.find('\n', next_line_start)
                    if next_line_end == -1:
                        next_line_end = len(content)

                    next_line = content[next_line_start:next_line_end]
                    indentation = len(next_line) - len(next_line.lstrip())

                    # Find where this indentation level ends
                    pos = next_line_end + 1
                    while pos < len(content):
                        line_start = pos
                        line_end = content.find('\n', line_start)
                        if line_end == -1:
                            line_end = len(content)

                        line = content[line_start:line_end]
                        if line.strip() and len(line) - len(line.lstrip()) <= indentation:
                            block_end = line_start - 1
                            break

                        pos = line_end + 1
                    else:
                        block_end = len(content)
                else:
                    # For languages with braces, find the matching closing brace
                    block_start = opening_bracket + 1
                    opening_count = 1
                    for j in range(block_start, len(content)):
                        if content[j] == '{':
                            opening_count += 1
                        elif content[j] == '}':
                            opening_count -= 1
                            if opening_count == 0:
                                block_end = j
                                break
                    else:
                        continue

                # Check if this block contains another loop
                block_content = content[block_start:block_end]
                inner_loops = re.search(loop_regex, block_content)

                if inner_loops:
                    inner_line = line_number + block_content[:inner_loops.start()].count('\n')
                    self.results['performance_issues'][file_path].append({
                        'type': 'nested_loops',
                        'description': f"Nested loops detected (outer loop at line {line_number}, inner at line {inner_line})",
                        'severity': 'high',
                        'line': line_number
                    })

        # Collect token statistics
        word_pattern = r'\b[a-zA-Z_]\w*\b'
        tokens = re.findall(word_pattern, content)
        token_freq = Counter(tokens)

        # Store the top 50 most common tokens
        for token, count in token_freq.most_common(50):
            self.results['token_stats'][token] += count

        # Calculate file complexity metrics
        # 1. Lines of code
        loc = len(lines)

        # 2. Comment density
        comment_lines = 0
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            is_comment = False
            for marker in markers:
                if line_stripped.startswith(marker):
                    is_comment = True
                    break

            if is_comment or in_block_comment:
                comment_lines += 1

            # Check for block comments
            if language in ['JavaScript', 'Java', 'C', 'C++', 'C#', 'PHP', 'Swift']:
                if '/*' in line_stripped and '*/' not in line_stripped[line_stripped.index('/*') + 2:]:
                    in_block_comment = True

                if '*/' in line_stripped and in_block_comment:
                    in_block_comment = False

        comment_density = comment_lines / loc if loc > 0 else 0

        # 3. Average line length
        non_empty_lines = [len(line) for line in lines if line.strip()]
        avg_line_length = sum(non_empty_lines) / len(non_empty_lines) if non_empty_lines else 0

        # Store metrics
        self.file_metrics[file_path] = {
            'loc': loc,
            'comment_lines': comment_lines,
            'comment_density': comment_density,
            'avg_line_length': avg_line_length
        }

    def _check_duplicated_code(self, file_path, content, language):
        """Check for duplicated code blocks"""
        # This is a simplified approach - real tools use more sophisticated algorithms
        # We'll use a line-based approach with a sliding window

        lines = content.split('\n')
        # Ignore comments and blank lines
        clean_lines = []

        comment_markers = {
            'Python': ['#'],
            'JavaScript': ['//', '/*'],
            'Java': ['//', '/*'],
            'C': ['//', '/*'],
            'C++': ['//', '/*'],
            'C#': ['//', '/*'],
            'Ruby': ['#'],
            'PHP': ['//', '/*', '#']
        }

        markers = comment_markers.get(language, ['#', '//'])
        in_block_comment = False

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                continue

            # Check for block comments
            if language in ['JavaScript', 'Java', 'C', 'C++', 'C#', 'PHP']:
                if '/*' in line_stripped and '*/' not in line_stripped[line_stripped.index('/*') + 2:]:
                    in_block_comment = True

                if '*/' in line_stripped and in_block_comment:
                    in_block_comment = False
                    continue

            # Skip comments
            is_comment = False
            for marker in markers:
                if line_stripped.startswith(marker):
                    is_comment = True
                    break

            if is_comment or in_block_comment:
                continue

            # Add non-comment line
            clean_lines.append(line_stripped)

        # Use a sliding window to find duplicated blocks
        # Minimum block size to consider
        min_block_size = 5

        for i in range(len(clean_lines) - min_block_size + 1):
            block = '\n'.join(clean_lines[i:i + min_block_size])

            # Skip if the block is too short or simple
            if len(block) < 100 or not re.search(r'[^\s\d\W]{3,}', block):
                continue

            # Hash the block for quicker comparison
            block_hash = hash(block)

            # Store the block with its location
            self.duplicated_blocks[block_hash].append({
                'file': file_path,
                'start_line': i + 1,
                'end_line': i + min_block_size,
                'content': block
            })

    def _analyze_duplicated_code(self):
        """Analyze collected duplicated code blocks and format for report"""
        final_duplicates = []
        reported_locations = set() # Keep track of (file, start_line) tuples already reported

        # Iterate through the raw data collected by _check_duplicated_code
        for block_hash, occurrences in self.duplicated_blocks.items(): # Use self.duplicated_blocks as in original
            if len(occurrences) > 1:
                # Basic filtering based on the first occurrence found
                representative_occurrence = occurrences[0]
                block_line_count = representative_occurrence['end_line'] - representative_occurrence['start_line'] + 1

                # Filter out very short blocks (adjust min_block_size if needed)
                min_block_size_report = 5 # You can adjust this threshold
                if block_line_count < min_block_size_report:
                    continue

                # --- Format for report - MATCH TEMPLATE KEYS ---
                locations_for_report = []
                for occ in occurrences:
                    # Create a unique identifier for this specific location instance
                    # Use 'file' key as per original _check_duplicated_code structure
                    loc_tuple = (occ['file'], occ['start_line'])
                    if loc_tuple not in reported_locations:
                        locations_for_report.append({
                            # Map original keys to template keys
                            'file_path': occ['file'],         # Template needs 'file_path'
                            'start_line': occ['start_line'],  # Template needs 'start_line'
                            'end_line': occ['end_line']     # Template needs 'end_line'
                        })
                        reported_locations.add(loc_tuple) # Mark this location as added

                # Only add if there are multiple *distinct* locations reported for this hash
                if len(locations_for_report) > 1:
                    # Estimate tokens (very crude - count words in the sample content)
                    # Use 'content' key as per original _check_duplicated_code structure
                    content_sample = representative_occurrence.get('content', '')
                    tokens_approx = len(re.findall(r'\w+', content_sample))

                    report_block = {
                        # Map original structure to template keys
                        'lines': block_line_count,              # Template needs 'lines'
                        'tokens': tokens_approx,                # Template needs 'tokens'
                        'files': locations_for_report,          # Template needs 'files' (list of location dicts)
                        'code_snippet': content_sample[:300] + ('...' if len(content_sample) > 300 else '') # Template needs 'code_snippet'
                    }
                    final_duplicates.append(report_block)

                    # Add code smells - only once per file for this duplication block
                    files_smelled_for_this_block = set()
                    for loc in locations_for_report:
                        # Use 'file_path' key here as it's what we added to locations_for_report
                        if loc['file_path'] not in files_smelled_for_this_block:
                            self.results['code_smells'][loc['file_path']].append({
                                'type': 'duplicate_code',
                                # Use report_block['lines'] as calculated above
                                'description': f"Part of duplicated code block ({report_block['lines']} lines) found in {len(locations_for_report)} location(s)",
                                'severity': 'high',
                                'line': loc['start_line'] # Report against start line
                            })
                            files_smelled_for_this_block.add(loc['file_path'])

        # Sort final list (e.g., by size) and store in results
        final_duplicates.sort(key=lambda x: (x['lines'], x['tokens']), reverse=True)
        self.results['duplicated_code'] = final_duplicates # Assign to the correct key in self.results
    def _analyze_dependencies(self):
        """Analyze project dependencies"""
        # No additional processing needed - dependencies were collected during file analysis
        pass

    def _identify_best_practices(self):
        """Identify relevant best practices for the project"""
        # Count languages to determine which best practices to include
        language_counts = defaultdict(int)

        for file_path in self.analyzed_files:
            ext = os.path.splitext(file_path)[1].lower()
            language = self._get_language_from_extension(ext)
            if language != "Unknown":
                language_counts[language.lower()] += 1

        # Include best practices for the used languages
        for language, count in language_counts.items():
            if language in BEST_PRACTICES:
                self.results['best_practices'][language] = BEST_PRACTICES[language]

    def _calculate_project_metrics(self):
        """Calculate overall project metrics"""
        if not self.file_metrics:
            return

        # Basic summaries
        total_loc = sum(m['loc'] for m in self.file_metrics.values())
        total_comment_lines = sum(m['comment_lines'] for m in self.file_metrics.values())

        # Calculate averages
        avg_comment_density = total_comment_lines / total_loc if total_loc > 0 else 0
        avg_line_length = sum(
            m['avg_line_length'] * m['loc'] for m in self.file_metrics.values()) / total_loc if total_loc > 0 else 0

        # Count issues by type
        code_smell_count = sum(len(smells) for smells in self.results['code_smells'].values())
        security_issue_count = sum(len(issues) for issues in self.results['security_issues'].values())
        performance_issue_count = sum(len(issues) for issues in self.results['performance_issues'].values())
        style_issue_count = sum(len(issues) for issues in self.results['style_issues'].values())

        # Calculate average function complexity
        all_functions = []
        for file_funcs in self.function_metrics.values():
            all_functions.extend(file_funcs.values())

        avg_function_complexity = sum(f.get('complexity', 0) for f in all_functions) / len(
            all_functions) if all_functions else 0
        avg_function_size = sum(f.get('lines', 0) for f in all_functions) / len(all_functions) if all_functions else 0
        avg_function_params = sum(f.get('params', 0) for f in all_functions) / len(
            all_functions) if all_functions else 0

        # Store metrics
        self.results['complexity_metrics'] = {
            'total_lines_of_code': total_loc,
            'total_comment_lines': total_comment_lines,
            'comment_density': avg_comment_density,
            'avg_line_length': avg_line_length,
            'code_smell_count': code_smell_count,
            'security_issue_count': security_issue_count,
            'performance_issue_count': performance_issue_count,
            'style_issue_count': style_issue_count,
            'avg_function_complexity': avg_function_complexity,
            'avg_function_size': avg_function_size,
            'avg_function_params': avg_function_params,
            'duplicated_code_blocks': len(self.results['duplicated_code'])
        }

        # Calculate a maintainability index (simplified version of the Microsoft metric)
        # Higher is better (more maintainable)
        v = avg_function_complexity  # Average cyclomatic complexity
        g = avg_line_length  # Average Halstead volume per function (we approximate with line length)
        l = total_loc  # Total lines of code
        cm = avg_comment_density  # Comment density

        maintainability = 171 - 5.2 * (v - 1) - 0.23 * g - 16.2 * (l / 1000) + 50 * cm
        self.results['complexity_metrics']['maintainability_index'] = min(100, max(0, maintainability))

        # Apply categorical rating
        rating_value = self.results['complexity_metrics']['maintainability_index']
        if rating_value >= 80:
            rating = "Excellent"
        elif rating_value >= 60:
            rating = "Good"
        elif rating_value >= 40:
            rating = "Fair"
        elif rating_value >= 20:
            rating = "Poor"
        else:
            rating = "Very Poor"

        self.results['complexity_metrics']['maintainability_rating'] = rating

        # Calculate a technical debt estimate (simplified)
        # Hours of work to fix issues, rough approximation
        issue_weights = {
            'critical': 8,  # 8 hours (full day) to fix critical issues
            'high': 4,  # 4 hours (half day) to fix high-severity issues
            'medium': 2,  # 2 hours to fix medium issues
            'low': 1  # 1 hour for low issues
        }

        total_debt_hours = 0

        # Count issues by severity
        for issues in self.results['code_smells'].values():
            for issue in issues:
                total_debt_hours += issue_weights.get(issue.get('severity', 'medium'), 2)

        for issues in self.results['security_issues'].values():
            for issue in issues:
                # Security issues get higher priority
                weight = issue_weights.get(issue.get('severity', 'high'), 4)
                total_debt_hours += weight * 1.5  # 50% extra for security

        for issues in self.results['performance_issues'].values():
            for issue in issues:
                total_debt_hours += issue_weights.get(issue.get('severity', 'medium'), 2)

        # Add estimated time for duplicated code
        total_debt_hours += len(self.results['duplicated_code']) * 3  # 3 hours per duplication to refactor

        self.results['complexity_metrics']['technical_debt_hours'] = total_debt_hours
        self.results['complexity_metrics']['technical_debt_days'] = round(total_debt_hours / 8, 1)  # 8-hour workdays

    def get_summary(self):
        """Get a summary of the analysis results"""
        if not self.results or 'complexity_metrics' not in self.results:
            return "No analysis results available."

        metrics = self.results['complexity_metrics']

        summary = [
            f"Project Analysis Summary:",
            f"- Total lines of code: {metrics.get('total_lines_of_code', 0):,}",
            f"- Files analyzed: {self.results['analysis_metadata'].get('files_analyzed', 0)}",
            f"- Comment density: {metrics.get('comment_density', 0):.1%}",
            f"- Maintainability rating: {metrics.get('maintainability_rating', 'Unknown')}",
            f"- Technical debt: {metrics.get('technical_debt_days', 0)} days",
            f"",
            f"Issues found:",
            f"- Code smells: {metrics.get('code_smell_count', 0)}",
            f"- Security issues: {metrics.get('security_issue_count', 0)}",
            f"- Performance issues: {metrics.get('performance_issue_count', 0)}",
            f"- Style issues: {metrics.get('style_issue_count', 0)}",
            f"- Duplicated code blocks: {metrics.get('duplicated_code_blocks', 0)}",
        ]

        # Add Rick quote
        rick_quotes = [
            "Wubba lubba dub dub! This code's got issues, but I've seen worse in the Citadel!",
            "Looks like someone coded this after visiting Blips and Chitz. *burp* Could use some cleanup.",
            "This code is like a Meeseeks box. Push the button and hope it doesn't create existential problems.",
            "In infinite dimensions, there's a version of this code that's perfect. This *burp* isn't it.",
            "Your technical debt is higher than my blood alcohol content... and that's saying something!"
        ]

        rating = metrics.get('maintainability_rating', '')
        if rating == "Excellent":
            quote = "Holy *burp* crap! This code is cleaner than the Citadel's bathrooms. And those are CLEAN."
        elif rating == "Good":
            quote = "Not bad. Your code is like the Microverse battery. Efficient, but still has some dark secrets."
        elif rating == "Fair":
            quote = "This code is like Jerry. It works, but nobody's excited about it."
        elif rating == "Poor":
            quote = "Your code's a bigger mess than my garage. And I turn people into *burp* insects in there!"
        elif rating == "Very Poor":
            quote = "I've seen better code written by Gazorpazorps! And they eat their young!"
        else:
            quote = random.choice(rick_quotes)

        summary.append(f"\nRick says: \"{quote}\"")

        return "\n".join(summary)

    def get_recommendations(self):
        """Get specific recommendations based on analysis"""
        if not self.results or 'complexity_metrics' not in self.results:
            return "No analysis results available for recommendations."

        recommendations = []

        # Add general recommendations based on issues found
        metrics = self.results['complexity_metrics']

        # 1. Code Smells
        if metrics.get('code_smell_count', 0) > 0:
            top_smells = Counter()
            for file_smells in self.results['code_smells'].values():
                for smell in file_smells:
                    top_smells[smell['type']] += 1

            most_common = top_smells.most_common(3)
            if most_common:
                recommendations.append("Code Smell Recommendations:")
                for smell_type, count in most_common:
                    if smell_type == 'long_function':
                        recommendations.append(
                            f"- Refactor {count} long functions by breaking them into smaller, more focused methods")
                    elif smell_type == 'too_many_parameters':
                        recommendations.append(
                            f"- Reduce parameter count in {count} functions by using parameter objects or restructuring")
                    elif smell_type == 'deep_nesting':
                        recommendations.append(
                            f"- Fix {count} instances of deep nesting by extracting methods or using early returns")
                    elif smell_type == 'duplicate_code':
                        recommendations.append(
                            f"- Eliminate {count} duplicated code blocks by creating reusable functions")
                    else:
                        recommendations.append(f"- Address {count} instances of '{smell_type}'")

        # 2. Security Issues
        if metrics.get('security_issue_count', 0) > 0:
            recommendations.append("\nSecurity Recommendations:")

            # Check for specific security issues
            has_sql_injection = False
            has_xss = False
            has_hardcoded_creds = False

            for file_issues in self.results['security_issues'].values():
                for issue in file_issues:
                    if issue['type'] == 'sql_injection':
                        has_sql_injection = True
                    elif issue['type'] == 'xss':
                        has_xss = True
                    elif issue['type'] == 'hardcoded_credentials':
                        has_hardcoded_creds = True

            if has_sql_injection:
                recommendations.append(
                    "- Use parameterized statements or ORM instead of string concatenation for SQL queries")

            if has_xss:
                recommendations.append("- Sanitize output and use safer DOM manipulation methods instead of innerHTML")

            if has_hardcoded_creds:
                recommendations.append(
                    "- Move hardcoded credentials to environment variables or a secure credential store")

            if metrics.get('security_issue_count', 0) > 3:
                recommendations.append("- Conduct a thorough security review and consider automated security scanning")

        # 3. Performance Issues
        if metrics.get('performance_issue_count', 0) > 0:
            recommendations.append("\nPerformance Recommendations:")
            has_nested_loops = False
            has_inefficient_loops = False

            for file_issues in self.results['performance_issues'].values():
                for issue in file_issues:
                    if issue['type'] == 'nested_loops':
                        has_nested_loops = True
                    elif issue['type'] == 'inefficient_loop':
                        has_inefficient_loops = True

            if has_nested_loops:
                recommendations.append("- Optimize nested loops to reduce algorithmic complexity")

            if has_inefficient_loops:
                recommendations.append("- Replace inefficient loop patterns with more optimized approaches")

        # 4. Style Issues
        if metrics.get('style_issue_count', 0) > 10:
            recommendations.append("\nStyle Recommendations:")
            recommendations.append("- Enforce a consistent code style across the project")
            recommendations.append("- Consider using a linter or automated formatter")

        # 5. Project-level recommendations
        recommendations.append("\nProject-level Recommendations:")

        # Comment density
        if metrics.get('comment_density', 0) < 0.1:
            recommendations.append("- Improve code documentation - current comment density is too low")

        # Technical debt
        if metrics.get('technical_debt_days', 0) > 10:
            recommendations.append(
                f"- Allocate time to address technical debt (estimated at {metrics.get('technical_debt_days', 0)} days)")

        # Maintainability
        rating = metrics.get('maintainability_rating', '')
        if rating in ["Poor", "Very Poor"]:
            recommendations.append("- Consider a significant refactoring effort to improve maintainability")

        # Add best practices from the language sections
        for language, practices in self.results.get('best_practices', {}).items():
            if practices:
                recommendations.append(f"\nBest Practices for {language.capitalize()}:")
                for practice in practices[:3]:  # Top 3 practices
                    recommendations.append(f"- {practice}")

        # Return formatted recommendations
        return "\n".join(recommendations)


# For standalone testing
if __name__ == "__main__":
    analyzer = AdvancedCodeAnalyzer()
    file_stats = {
        'test.py': {
            'name': 'test.py',
            'path': 'test.py',
            'lines': 100,
            'language': 'Python'
        }
    }
    results = analyzer.analyze_project(".", file_stats)
    print(analyzer.get_summary())
    print("\n")
    print(analyzer.get_recommendations())