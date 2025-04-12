#!/usr/bin/env python3
# Fun Code Analyzer Module for Rick's Code Analyzer
# Adds humorous and thematic analysis tools

import os
import re
import random
import chardet
from collections import defaultdict, Counter
import datetime

# Rick & Morty themed keywords/phrases (case-insensitive)
RICK_KEYWORDS = [
    'rick', 'morty', 'schwifty', 'wubba lubba dub dub', 'get schwifty',
    'pickle rick', 'plumbus', 'meeseeks', 'gazorpazorp', 'squanch',
    'cronenberg', 'birdperson', 'unity', 'jerry', 'beth', 'summer',
    'portal gun', 'interdimensional', 'council of ricks', 'citadel',
    'tiny rick', 'anatomy park', 'blips and chitz'
]

# Patterns indicative of potentially overly simple or redundant ("Jerry-like") code
JERRY_PATTERNS = [
    (r'\bif\s+True\b', "if True: condition - always executes"),
    (r'\bwhile\s+True\b', "while True: loop - potentially infinite without break"),
    (r'(\w+)\s*=\s*\1\b', "Variable assigned to itself (e.g., x = x)"),
    (r'return\s+None\b', "Explicitly returning None (often redundant)"),
    (r'\w+\s*==\s*\w+\b', "Comparing a variable to itself (e.g., x == x)"), # Very basic check
]

# Common "colorful" words (censored for display)
SWEAR_WORDS = [
    'f***', 's***', 'a**', 'b****', 'c***', 'd***', 'hell', 'damn'
    # Add more as desired, keeping them censored/mild
]

# TODO/FIXME Markers
TASK_MARKERS = ['TODO', 'FIXME', 'HACK', 'XXX', 'NOTE']

# Code Personality Traits (based on simple heuristics)
PERSONALITIES = {
    'Cynical Rick': "Dominated by short functions, minimal comments, maybe some 'HACK' tags. Gets the job done, doesn't care how.",
    'Anxious Morty': "Lots of comments, potentially long functions, maybe 'FIXME' tags. Tries hard, maybe too hard.",
    'Methodical Beth': "Balanced comments and code, consistent naming, clear structure. Organized and competent.",
    'Overconfident Summer': "Uses modern syntax (if detectable), maybe fewer comments assuming code is self-explanatory.",
    'Simple Jerry': "Lots of simple patterns detected, potentially redundant code, maybe overly verbose comments for simple things.",
    'Chaotic Neutral': "A mix of everything, inconsistent style. Hard to pin down, like Rick on a bender."
}

# --- Helper Functions ---

def detect_encoding(file_path):
    """Detects the encoding of a file."""
    try:
        with open(file_path, 'rb') as f:
            raw_content = f.read(4096) # Read first 4k bytes
        result = chardet.detect(raw_content)
        encoding = result['encoding'] if result and result['encoding'] else 'utf-8'
        # Handle specific cases or provide default
        if encoding.lower() == 'ascii':
            encoding = 'utf-8' # Treat ascii as utf-8 subset
        return encoding
    except Exception:
        return 'utf-8' # Default fallback

def read_file_content(file_path):
    """Reads file content with detected encoding."""
    encoding = detect_encoding(file_path)
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            return f.read()
    except Exception as e:
        # Fallback if primary read fails
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as fallback_e:
            print(f"ERROR: Could not read file {file_path} with encoding {encoding} or utf-8: {fallback_e}")
            return None # Indicate failure

# --- Main Analyzer Class ---

class FunCodeAnalyzer:
    """Provides fun and thematic code analysis."""

    def __init__(self, callback_function=None):
        """Initialize the fun analyzer.

        Args:
            callback_function: Function to call for progress updates.
        """
        self.callback = callback_function
        self.results = {
            'rick_references': defaultdict(list),
            'jerry_detections': defaultdict(list),
            'swear_counts': defaultdict(int),
            'task_markers': defaultdict(lambda: defaultdict(int)),
            'code_personality': {},
            'overall_fun_score': 0,
            'fun_quote': ""
        }
        # Track stats for personality analysis
        self._file_comment_density = {}
        self._file_avg_line_length = {}
        self._file_naming_styles = defaultdict(lambda: Counter()) # file -> style -> count

    def update_progress(self, message):
        """Update progress via callback."""
        if self.callback:
            self.callback(message)
        else:
            print(message)

    def analyze_project(self, project_path, file_stats):
        """Run fun analysis on the project.

        Args:
            project_path: Path to the project directory.
            file_stats: Dictionary of file statistics from basic analysis.

        Returns:
            Dictionary containing fun analysis results.
        """
        self.update_progress("Starting Fun Analysis... Wubba Lubba Dub Dub!")

        files_to_analyze = list(file_stats.keys())

        for file_path in files_to_analyze:
            self.update_progress(f"Fun-alyzing: {os.path.basename(file_path)}")
            content = read_file_content(file_path)
            if content is None:
                continue # Skip if file couldn't be read

            language = file_stats[file_path].get('language', 'Unknown')
            lines = content.splitlines()

            self._find_rick_references(file_path, content)
            self._detect_jerry_code(file_path, content)
            self._count_swear_words(file_path, content)
            self._analyze_task_markers(file_path, content)
            self._gather_personality_metrics(file_path, lines, language)

        self._determine_code_personalities(file_stats)
        self._calculate_fun_score()
        self._select_fun_quote()

        self.update_progress("Fun Analysis Complete! Hope you didn't find any Cronenbergs.")
        return self.results

    def _find_rick_references(self, file_path, content):
        """Find Rick & Morty keywords in comments and strings."""
        # Regex to find comments (simple version for common languages)
        # Handles //, #, /* ... */ (non-nested), Python """ """, ''' '''
        comment_regex = r'(#.*)|(//.*)|(/\*.*?\*/)|("""(.*?)""")|(\'\'\'(.*?)\'\'\')'
        # Regex to find basic string literals
        string_regex = r'(".*?")|(\'.*?\')|(`.*?`)' # Includes template literals

        combined_regex = f"({comment_regex})|({string_regex})"

        for match in re.finditer(combined_regex, content, re.IGNORECASE | re.DOTALL):
            text_segment = match.group(0)
            line_number = content[:match.start()].count('\n') + 1

            for keyword in RICK_KEYWORDS:
                # Use word boundaries for keywords to avoid partial matches (like 'rick' in 'brick')
                # unless the keyword has spaces
                pattern = r'\b' + re.escape(keyword) + r'\b' if ' ' not in keyword else re.escape(keyword)
                if re.search(pattern, text_segment, re.IGNORECASE):
                    self.results['rick_references'][file_path].append({
                        'line': line_number,
                        'keyword': keyword,
                        'context': text_segment[:100].strip() + ('...' if len(text_segment) > 100 else '')
                    })

    def _detect_jerry_code(self, file_path, content):
        """Detect patterns that might indicate overly simple or redundant code."""
        for pattern, description in JERRY_PATTERNS:
            try: # Regex can sometimes fail on complex patterns
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    line_number = content[:match.start()].count('\n') + 1
                    self.results['jerry_detections'][file_path].append({
                        'line': line_number,
                        'description': description,
                        'match': match.group(0)[:80] # Show matched text
                    })
            except Exception as e:
                 self.update_progress(f"Regex warning for Jerry pattern '{description}' in {file_path}: {e}")


    def _count_swear_words(self, file_path, content):
        """Count occurrences of predefined swear words."""
        count = 0
        # More robust search, ignoring case and ensuring whole words
        for word in SWEAR_WORDS:
            # Escape potential regex characters in the word, handle '*' as wildcard
            safe_word = re.escape(word).replace(r'\*', r'\w*')
            pattern = r'\b' + safe_word + r'\b'
            matches = re.findall(pattern, content, re.IGNORECASE)
            count += len(matches)
        if count > 0:
            self.results['swear_counts'][file_path] = count

    def _analyze_task_markers(self, file_path, content):
        """Find and categorize TODO, FIXME, etc. markers in comments."""
         # Simple comment regex: #, //, /* ... */
        comment_regex = r'(?:#|//).*|(/\*.*?\*/)'
        for match in re.finditer(comment_regex, content, re.DOTALL):
            comment_text = match.group(0)
            line_number = content[:match.start()].count('\n') + 1

            for marker in TASK_MARKERS:
                # Look for marker at start of comment or after non-alphanumeric chars
                pattern = r'(?:\W|^)' + marker + r'[:\s]'
                if re.search(pattern, comment_text, re.IGNORECASE):
                    self.results['task_markers'][file_path][marker] += 1
                    # Optional: Extract the text after the marker
                    # marker_pos = comment_text.upper().find(marker)
                    # task_text = comment_text[marker_pos + len(marker):].strip(': ')[:80]


    def _gather_personality_metrics(self, file_path, lines, language):
        """Calculate metrics needed for personality analysis."""
        loc = len(lines)
        if loc == 0: return

        # Comment Density (simple line count)
        comment_lines = 0
        comment_markers = {'Python': '#', 'JavaScript': '//', 'Java': '//', 'C++': '//', 'C#': '//', 'Ruby': '#', 'PHP': '//'} # Simplified
        marker = comment_markers.get(language, '#')
        for line in lines:
            if line.strip().startswith(marker):
                comment_lines += 1
        self._file_comment_density[file_path] = comment_lines / loc

        # Average Line Length
        non_empty_lines = [len(line) for line in lines if line.strip()]
        self._file_avg_line_length[file_path] = sum(non_empty_lines) / len(non_empty_lines) if non_empty_lines else 0

        # Naming Styles (very basic check on variable/function names)
        # Look for patterns like var_name, varName, VAR_NAME
        content = "\n".join(lines)
        snake_case = len(re.findall(r'\b[a-z0-9]+(?:_[a-z0-9]+)+\b', content))
        camel_case = len(re.findall(r'\b[a-z]+(?:[A-Z][a-z0-9]*)+\b', content))
        pascal_case = len(re.findall(r'\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)*\b', content)) # Often classes
        screaming_snake = len(re.findall(r'\b[A-Z0-9]+(?:_[A-Z0-9]+)+\b', content)) # Often constants

        self._file_naming_styles[file_path]['snake'] = snake_case
        self._file_naming_styles[file_path]['camel'] = camel_case
        self._file_naming_styles[file_path]['pascal'] = pascal_case
        self._file_naming_styles[file_path]['screaming'] = screaming_snake


    def _determine_code_personalities(self, file_stats):
        """Assign a personality to each analyzed file."""
        for file_path in file_stats.keys():
            if file_path not in self._file_comment_density: continue # Skip if metrics weren't gathered

            density = self._file_comment_density[file_path]
            avg_len = self._file_avg_line_length[file_path]
            naming = self._file_naming_styles[file_path]
            tasks = self.results['task_markers'][file_path]
            jerry_hits = len(self.results['jerry_detections'].get(file_path, []))

            # Simple Heuristics
            if jerry_hits > 2 and density > 0.2:
                personality = 'Simple Jerry'
            elif tasks.get('HACK', 0) > 0 and density < 0.05 and avg_len < 70:
                personality = 'Cynical Rick'
            elif tasks.get('FIXME', 0) > 1 and density > 0.15:
                 personality = 'Anxious Morty'
            elif density > 0.1 and density < 0.25 and sum(naming.values()) > 10: # Check if naming conventions seem consistent
                 # Basic check for consistency: one style is dominant
                 styles = sorted(naming.items(), key=lambda item: item[1], reverse=True)
                 if len(styles) > 0 and styles[0][1] > sum(s[1] for s in styles[1:]) * 1.5 : # If largest is 1.5x rest combined
                     personality = 'Methodical Beth'
                 else:
                      personality = 'Chaotic Neutral' # Inconsistent naming
            elif density < 0.08:
                 personality = 'Overconfident Summer'
            else:
                 personality = 'Chaotic Neutral' # Default fallback

            self.results['code_personality'][file_path] = personality


    def _calculate_fun_score(self):
        """Calculate a totally arbitrary 'Fun Score'."""
        score = 50 # Start neutral

        # Rick references are good (thematically)
        score += len(self.results['rick_references']) * 2

        # Jerry code is bad (usually)
        score -= sum(len(v) for v in self.results['jerry_detections'].values()) * 3

        # Swearing adds chaos points!
        score += sum(self.results['swear_counts'].values()) * 1

        # Task markers show awareness, but too many FIXMEs might be Morty-level anxiety
        score += sum(v.get('TODO', 0) + v.get('NOTE', 0) for v in self.results['task_markers'].values()) * 0.5
        score -= sum(v.get('FIXME', 0) for v in self.results['task_markers'].values()) * 1
        score += sum(v.get('HACK', 0) for v in self.results['task_markers'].values()) * 1 # Hacks are Rick-like

        # Personalities influence score
        personality_counts = Counter(self.results['code_personality'].values())
        score += personality_counts.get('Cynical Rick', 0) * 2
        score += personality_counts.get('Methodical Beth', 0) * 3
        score -= personality_counts.get('Anxious Morty', 0) * 1
        score -= personality_counts.get('Simple Jerry', 0) * 5
        score += personality_counts.get('Overconfident Summer', 0) * 1
        # Chaotic Neutral doesn't change score much

        self.results['overall_fun_score'] = max(0, min(100, int(score))) # Clamp score 0-100

    def _select_fun_quote(self):
        """Select a fun quote based on the score."""
        score = self.results['overall_fun_score']
        if score > 85:
            quote = "This code is schwifty! It's got the right amount of chaos and references. Approved!"
        elif score > 65:
            quote = "Alright, alright, this code's got some personality. Less Jerry, more... well, not *totally* disastrous."
        elif score > 40:
            quote = "Meh. It's code. It exists. Doesn't exactly scream 'interdimensional adventure', does it?"
        elif score > 20:
            quote = "Looks like Jerry might've *burp* had a hand in this. Too much simplicity, not enough questionable life choices."
        else:
            quote = "Yikes. This code is about as fun as a Kronenberg universe. Needs a serious injection of... something."

        # Add a random element
        if random.random() < 0.1: # 10% chance of generic Rick quote
             quote += " Also, Wubba Lubba Dub Dub!"

        self.results['fun_quote'] = quote


    def get_fun_summary(self):
        """Generate a text summary of the fun analysis results."""
        summary = []
        summary.append("--- RICK'S FUN ANALYSIS ---")
        summary.append(f"Overall Fun Score: {self.results['overall_fun_score']}/100")
        summary.append(f"Rick's Verdict: \"{self.results['fun_quote']}\"")
        summary.append("-" * 25)

        # Rick References
        ref_count = sum(len(v) for v in self.results['rick_references'].values())
        if ref_count > 0:
            summary.append(f"Found {ref_count} Rick & Morty references!")
            for file, refs in self.results['rick_references'].items():
                if refs:
                     summary.append(f"  - {os.path.basename(file)}: {len(refs)} references (e.g., '{refs[0]['keyword']}' on line {refs[0]['line']})")

        # Jerry Detections
        jerry_count = sum(len(v) for v in self.results['jerry_detections'].values())
        if jerry_count > 0:
             summary.append(f"\nDetected {jerry_count} potential 'Jerry-like' code patterns:")
             count = 0
             for file, detects in self.results['jerry_detections'].items():
                 if detects and count < 3: # Show details for first few files
                     summary.append(f"  - {os.path.basename(file)}: {len(detects)} instances (e.g., '{detects[0]['description']}' on line {detects[0]['line']})")
                     count += 1
             if jerry_count > 3 : summary.append("   (and more...)")


        # Swear Counts
        swear_total = sum(self.results['swear_counts'].values())
        if swear_total > 0:
            summary.append(f"\nDetected {swear_total} instances of *colorful* language.")
            top_files = sorted(self.results['swear_counts'].items(), key=lambda item: item[1], reverse=True)[:3]
            for file, count in top_files:
                 summary.append(f"  - {os.path.basename(file)}: {count} instances")

        # Task Markers
        task_total = sum(sum(f.values()) for f in self.results['task_markers'].values())
        if task_total > 0:
            summary.append(f"\nFound {task_total} task markers (TODO, FIXME, etc.):")
            marker_counts = Counter()
            for file_markers in self.results['task_markers'].values():
                marker_counts.update(file_markers)
            for marker, count in marker_counts.most_common():
                summary.append(f"  - {marker}: {count} times")

        # Code Personalities
        if self.results['code_personality']:
            summary.append("\nCode Personality Analysis:")
            personality_counts = Counter(self.results['code_personality'].values())
            for personality, count in personality_counts.most_common():
                summary.append(f"  - {personality}: {count} file(s)")
                # Show one example file for the most common personality
                if personality == personality_counts.most_common(1)[0][0]:
                     example_file = next((f for f, p in self.results['code_personality'].items() if p == personality), None)
                     if example_file:
                         summary.append(f"    (e.g., {os.path.basename(example_file)})")


        summary.append("\n--- END OF FUN ANALYSIS ---")
        return "\n".join(summary)

    def get_html_report_data(self):
        """Formats the fun analysis results for the HTML template."""
        # Flatten references and detections for easier looping in template
        all_refs = []
        for file, refs in self.results['rick_references'].items():
            for ref in refs:
                all_refs.append({
                    'file': os.path.basename(file),
                    'line': ref['line'],
                    'keyword': ref['keyword'],
                    'context': ref['context']
                })

        all_jerry = []
        for file, detects in self.results['jerry_detections'].items():
            for det in detects:
                all_jerry.append({
                    'file': os.path.basename(file),
                    'line': det['line'],
                    'description': det['description'],
                    'match': det['match']
                })

        # Structure swear counts
        swear_list = [{'file': os.path.basename(f), 'count': c}
                      for f, c in self.results['swear_counts'].items()]
        swear_list.sort(key=lambda x: x['count'], reverse=True)

        # Structure task markers
        marker_summary = Counter()
        for file_markers in self.results['task_markers'].values():
            marker_summary.update(file_markers)
        marker_list = [{'marker': m, 'count': c}
                       for m, c in marker_summary.items()]
        marker_list.sort(key=lambda x: x['count'], reverse=True)

        # Group files by personality
        personality_groups = defaultdict(list)
        for file, personality in self.results['code_personality'].items():
            personality_groups[personality].append(os.path.basename(file))

        return {
            'fun_score': self.results['overall_fun_score'],
            'fun_quote': self.results['fun_quote'],
            'rick_references': all_refs,
            'jerry_detections': all_jerry,
            'swear_counts': swear_list,
            'swear_total': sum(self.results['swear_counts'].values()),
            'task_markers': marker_list,
            'task_total': sum(sum(f.values()) for f in self.results['task_markers'].values()),
            'personality_groups': dict(personality_groups),  # Convert back to dict for template
            'personalities_desc': PERSONALITIES,
            'current_year': datetime.datetime.now().year  # Added for footer consistency
        }

# --- Standalone Testing ---
if __name__ == "__main__":
    print("Running Fun Analyzer Standalone Test...")

    # Create dummy files for testing
    if not os.path.exists("fun_test_project"):
        os.makedirs("fun_test_project")

    with open("fun_test_project/rick_stuff.py", "w") as f:
        f.write("# TODO: Get schwifty in here!\n")
        f.write("import os\n\n")
        f.write("def pickle_rick():\n")
        f.write("    # This is the peak of science\n")
        f.write("    print('I am Pickle Rick!')\n")
        f.write("    useless_var = useless_var # Jerry code\n")
        f.write("    if True:\n        print('Duh')\n")
        f.write("    # FIXME: This logic is maybe bad?\n")
        f.write("    return None\n")

    with open("fun_test_project/morty_math.js", "w") as f:
        f.write("// Oh geez, I hope this works\n")
        f.write("function add(a, b) {\n")
        f.write("  // This is addition, Morty! Basic stuff!\n")
        f.write("  console.log('Adding...'); // NOTE: Debug log\n")
        f.write("  let result = a + b;\n")
        f.write("  if (result === result) { /* Sanity check? */ }\n")
        f.write("  // What the f*** is this supposed to do?\n")
        f.write("  return result; // Should be okay?\n")
        f.write("}\n")
        f.write("const x = 5; // XXX: Magic number?\n")

    # Create dummy file stats
    dummy_file_stats = {
        os.path.abspath("fun_test_project/rick_stuff.py"): {
            'name': 'rick_stuff.py',
            'path': os.path.abspath("fun_test_project/rick_stuff.py"),
            'lines': 9, 'code': 5, 'comments': 3, 'blank': 1, 'language': 'Python'
            },
        os.path.abspath("fun_test_project/morty_math.js"): {
            'name': 'morty_math.js',
            'path': os.path.abspath("fun_test_project/morty_math.js"),
            'lines': 8, 'code': 5, 'comments': 3, 'blank': 0, 'language': 'JavaScript'
            },
    }

    analyzer = FunCodeAnalyzer(print) # Use print as the callback
    results = analyzer.analyze_project(os.path.abspath("fun_test_project"), dummy_file_stats)

    print("\n--- Fun Analysis Results ---")
    # Basic print of the results dictionary
    # import json
    # print(json.dumps(results, indent=2))

    print("\n--- Fun Summary ---")
    print(analyzer.get_fun_summary())

    # Clean up dummy files
    # import shutil
    # shutil.rmtree("fun_test_project")
    print("\nStandalone test finished.")