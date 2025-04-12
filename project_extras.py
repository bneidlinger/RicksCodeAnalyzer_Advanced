#!/usr/bin/env python3
# Project Extras Module for Rick's Code Analyzer
# Handles dependency scanning and visualization data preparation

import os
import subprocess
import json
import sys
from collections import defaultdict

# --- Dependency Security Scanning (Python/Safety) ---

def find_requirements_file(project_path):
    """Finds common Python requirements files."""
    common_files = ['requirements.txt', 'requirements.in', 'pyproject.toml']
    for filename in common_files:
        req_path = os.path.join(project_path, filename)
        if os.path.isfile(req_path):
            return req_path, filename
    return None, None

def run_safety_check(project_path, callback_function=None):
    """Runs 'safety check' on the project's requirements file."""
    results = {
        'vulnerabilities': [],
        'error': None,
        'checked_file': None,
        'safety_version': None,
        'status': 'Not Run'
    }

    def update_progress(msg):
        if callback_function:
            callback_function(f"  [Safety] {msg}")
        else:
            print(f"  [Safety] {msg}")

    update_progress("Looking for Python dependency file...")
    req_path, req_filename = find_requirements_file(project_path)

    if not req_path:
        results['error'] = "No common Python dependency file found (requirements.txt, etc.)."
        results['status'] = 'No File'
        update_progress(results['error'])
        return results

    results['checked_file'] = req_filename
    update_progress(f"Found: {req_filename}. Checking for 'safety' tool...")

    try:
        # Check if safety is installed and get version
        version_process = subprocess.run([sys.executable, '-m', 'safety', '--version'], capture_output=True, text=True, check=False)
        if version_process.returncode != 0:
             raise FileNotFoundError("Safety command failed")
        results['safety_version'] = version_process.stdout.strip()
        update_progress(f"Using safety version: {results['safety_version']}")

        # Command to run safety check and output JSON
        # Using sys.executable ensures we use the python/pip associated with the script runner
        # Add --ignore 41002 for now, as 'requests' often triggers it and it's sometimes ignorable
        # Add --ignore 39462 for older jinja2 if needed
        # Using full path to requirements file is safer
        command = [
            sys.executable, '-m', 'safety', 'check',
            '--file', req_path,
            '--output', 'json',
            '--ignore', '41002', # Ignore common 'requests' http verb warning
            '--ignore', '39462'  # Ignore older Jinja2 escape warning if present
        ]

        update_progress(f"Running command: {' '.join(command)}")
        process = subprocess.run(command, capture_output=True, text=True, check=False) # Don't check=True, handle errors manually

        if process.returncode == 0:
            update_progress("Safety check completed successfully (no vulnerabilities found).")
            results['status'] = 'Secure'
            # Try parsing output even if return code is 0, might contain scan metadata
            try:
                 scan_data = json.loads(process.stdout)
                 # You could extract scan metadata here if needed
            except json.JSONDecodeError:
                 update_progress("Could not parse safety JSON output (empty?).")
        elif process.stdout:
            update_progress("Safety check completed. Found potential vulnerabilities.")
            results['status'] = 'Vulnerable'
            try:
                parsed_json = json.loads(process.stdout)
                # Safety JSON output structure (list of vulnerabilities):
                # [ [package_name, affected_versions, installed_version, description, vulnerability_id], ... ]
                for vuln in parsed_json:
                     if len(vuln) >= 5:
                         results['vulnerabilities'].append({
                             'package': vuln[0],
                             'affected': vuln[1],
                             'installed': vuln[2],
                             'description': vuln[3],
                             'id': vuln[4]
                         })
                     else:
                          update_progress(f"Skipping malformed vulnerability data: {vuln}")

            except json.JSONDecodeError as json_err:
                results['error'] = f"Failed to parse safety JSON output: {json_err}. Raw output:\n{process.stdout[:500]}"
                results['status'] = 'Error'
                update_progress(results['error'])
            except Exception as e:
                 results['error'] = f"Unexpected error processing safety output: {e}"
                 results['status'] = 'Error'
                 update_progress(results['error'])
        else:
            # Handle cases where safety fails to run (e.g., file not found by safety itself)
            error_output = process.stderr if process.stderr else "Unknown error (no stdout/stderr)"
            results['error'] = f"Safety check command failed (return code {process.returncode}). Error: {error_output.strip()}"
            results['status'] = 'Error'
            update_progress(results['error'])

    except FileNotFoundError:
        results['error'] = "'safety' command not found. Install with 'pip install safety'"
        results['status'] = 'Error'
        update_progress(results['error'])
    except Exception as e:
        results['error'] = f"An unexpected error occurred during safety check: {e}"
        results['status'] = 'Error'
        update_progress(results['error'])

    return results


# --- Dependency Graph Data Preparation ---

def prepare_graph_data(import_graph, project_path):
    """Formats the import graph for vis.js, handling simple relative imports."""
    nodes = []
    edges = []
    node_map = {} # Map full file path to unique node ID
    path_to_node_id = {} # Reverse map for easier lookup

    project_root_norm = os.path.normpath(project_path)

    # --- Pass 1: Create nodes for all analyzed files ---
    node_id_counter = 1
    for file_path_abs in import_graph.keys():
        # Ensure keys are absolute paths for reliable matching
        if not os.path.isabs(file_path_abs): continue # Should be absolute from analyzer

        node_id = node_id_counter
        node_map[file_path_abs] = node_id
        path_to_node_id[file_path_abs] = node_id # Store reverse mapping

        # Try to get relative path, fallback to basename
        try:
            relative_path = os.path.relpath(file_path_abs, project_root_norm)
        except ValueError: # Handle cases where file is outside project path (e.g. temp files?)
            relative_path = os.path.basename(file_path_abs)

        nodes.append({
            'id': node_id,
            'label': relative_path.replace('\\', '/'), # Display relative path with forward slashes
            'title': file_path_abs # Tooltip shows full path
        })
        node_id_counter += 1

    # --- Pass 2: Create edges ---
    for importer_path_abs, imported_modules in import_graph.items():
        importer_id = node_map.get(importer_path_abs)
        if not importer_id: continue # Skip if importer wasn't mapped (shouldn't happen)

        importer_dir_abs = os.path.dirname(importer_path_abs)

        for module_name in imported_modules:
            if not module_name: continue # Skip empty module names

            target_path_abs = None
            target_id = None

            # --- Attempt to resolve module name to an analyzed file path ---

            # 1. Handle Relative Imports (starting with '.')
            if module_name.startswith('.'):
                level = 0
                while module_name.startswith('.'):
                    level += 1
                    module_name = module_name[1:]

                # Calculate base directory based on levels
                current_dir = importer_dir_abs
                for _ in range(level - 1): # Go up N-1 levels for N dots
                    current_dir = os.path.dirname(current_dir)

                # Construct potential path parts
                module_parts = module_name.split('.') if module_name else []
                potential_path_abs = os.path.normpath(os.path.join(current_dir, *module_parts))

                # Check if this path (as .py or as package/__init__.py) exists in our node map
                potential_py_file = potential_path_abs + ".py"
                potential_init_file = os.path.join(potential_path_abs, "__init__.py")

                if potential_py_file in node_map:
                    target_path_abs = potential_py_file
                elif potential_init_file in node_map:
                    target_path_abs = potential_init_file

            # 2. Handle Absolute-like Imports (treat as relative to project root)
            else:
                module_parts = module_name.split('.')
                potential_path_abs = os.path.normpath(os.path.join(project_root_norm, *module_parts))

                 # Check if this path (as .py or as package/__init__.py) exists in our node map
                potential_py_file = potential_path_abs + ".py"
                potential_init_file = os.path.join(potential_path_abs, "__init__.py")

                if potential_py_file in node_map:
                    target_path_abs = potential_py_file
                elif potential_init_file in node_map:
                    target_path_abs = potential_init_file

                # Add more sophisticated checks here if needed (e.g., checking sys.path, src layout)


            # --- If a matching analyzed file was found, add the edge ---
            if target_path_abs:
                target_id = node_map.get(target_path_abs)
                if target_id:
                    # Avoid self-loops (though unlikely with imports)
                    if importer_id != target_id:
                        edges.append({'from': importer_id, 'to': target_id})
                # else: # Debugging if path found but not in node_map
                #     print(f"WARN: Resolved path '{target_path_abs}' not found in node_map.")

            # else: # Debugging: Module not resolved to an internal file
            #    print(f"DEBUG: No internal file match for module '{module_name}' from '{os.path.basename(importer_path_abs)}'")


    # Deduplicate edges (in case logic adds the same edge twice)
    unique_edges = []
    seen_edges = set()
    for edge in edges:
        edge_tuple = (edge['from'], edge['to'])
        if edge_tuple not in seen_edges:
            unique_edges.append(edge)
            seen_edges.add(edge_tuple)

    return {'nodes': nodes, 'edges': unique_edges}


# --- Standalone Testing ---
if __name__ == "__main__":
    print("Running Project Extras Standalone Test...")
    # Create dummy requirements
    if not os.path.exists("extras_test"): os.makedirs("extras_test")
    with open("extras_test/requirements.txt", "w") as f:
        f.write("flask==1.0.0\n") # Known vulnerable version
        f.write("requests>=2.20\n")

    print("\n--- Testing Safety Check ---")
    safety_results = run_safety_check("extras_test", print)
    print("\nSafety Results:")
    print(json.dumps(safety_results, indent=2))

    print("\n--- Testing Graph Prep ---")
    # Dummy import graph
    dummy_graph = {
        os.path.abspath("extras_test/app.py"): {'utils', 'models.user', 'flask'},
        os.path.abspath("extras_test/utils.py"): {'os', 'datetime'},
        os.path.abspath("extras_test/models/user.py"): {'sqlalchemy'}
    }
    graph_data = prepare_graph_data(dummy_graph, os.path.abspath("extras_test"))
    print("\nGraph Data for vis.js:")
    print(json.dumps(graph_data, indent=2))

    # Clean up
    import shutil
    # shutil.rmtree("extras_test")
    print("\nStandalone test finished.")