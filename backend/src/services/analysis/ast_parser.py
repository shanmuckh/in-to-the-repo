import os
from typing import Dict, List, Optional, Any
from tree_sitter import Language, Parser
import time
import tree_sitter_java as tsjava
import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
import tree_sitter_javascript as tsjavascript
import tree_sitter_python as tspython
import tree_sitter_typescript as tstypescript
from src.config.language_node_maps import language_node_maps
from src.services.analysis.file_graph_generator import build_dependency_graph
from src.services.utilities.git_utils import get_file_git_info
from src.services.analysis.parse_utils import extract_import_data
from typing import Callable
from src.core.logging import get_logger

logger = get_logger(__name__)


LANGUAGE_LOADING_MESSAGES = {
    "cpp": "C++ detected — where one wrong pointer ruins your day 😅",
    "c": "C detected — manual memory management zone 🧠💥",
    "java": "Java detected. Hold tight, this might take a while ⏳",
    "python": "Python detected. Smooth ride incoming 🐍",
    "javascript": "JavaScript detected — semicolons are optional, bugs are not 😜",
    "typescript": "TypeScript detected — now with types and twice the compile time ⌛",
    "tsx": "TSX detected — React and TypeScript? Brave soul 👨‍🚀"
}


LANGUAGE_GRAMMARS = {
    "python": tspython.language(),
    "javascript": tsjavascript.language(),
    "typescript": tstypescript.language_typescript(),
    "tsx": tstypescript.language_tsx(),
    "java": tsjava.language(),
    "cpp": tscpp.language(),
    "c": tsc.language(),
}

LANGUAGE_FILE_EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js", ".jsx"],
    "typescript": [".ts"],
    "tsx": [".tsx"],
    "java": [".java"],
    "cpp": [".cpp", ".hpp"],
    "c": [".c", ".h"],
}

parser_cache = {}

def get_parser(language):
    if language in parser_cache:
        return parser_cache[language]
    try:
        grammar_path = LANGUAGE_GRAMMARS[language]
        lang_obj = Language(grammar_path)
        parser = Parser(lang_obj)
        parser_cache[language] = parser
        return parser
    except KeyError:
        raise ValueError(f"Unsupported language: {language}")
    except TypeError:
        raise ValueError(f"Invalid grammar path for {language}: {grammar_path}")



def calculate_complexity(node):
    """Calculate simplified cyclomatic complexity"""
    complexity = 1
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type in ("if_statement", "for_statement", "while_statement"):
            complexity += 1
        stack.extend(current.children)
    return complexity

def detect_file_language(filename: str):
    for language, extensions in LANGUAGE_FILE_EXTENSIONS.items():
        if any(filename.endswith(ext) for ext in extensions):
            return language
    return None



def extract_methods(node):
    """Helper function to extract methods from a class node."""
    methods = []
    for child in node.children:
        if child.type in ["function_definition", "method_definition"]:
            method_name = child.child_by_field_name("name").text.decode()
            methods.append(method_name)
    return methods

def extract_callee_name(call_node):
    """
    Given a call_expression node, extract a readable callee name.
    """
    callee_node = call_node.child_by_field_name("function") or call_node.child_by_field_name("callee") or call_node.children[0]

    if callee_node is None:
        callee_node = call_node.children[0]

    return get_node_name(callee_node)

def get_node_name(node):
    """
    Recursively convert a node to a string representing the callee name.
    Supports identifiers, member expressions, etc.
    """
    if node.type == "identifier":
        return node.text.decode()

    if node.type == "member_expression":
        object_node = node.child_by_field_name("object")
        property_node = node.child_by_field_name("property")
        object_name = get_node_name(object_node) if object_node else ""
        property_name = get_node_name(property_node) if property_node else ""
        if object_name and property_name:
            return f"{object_name}.{property_name}"
        return object_name or property_name

    if node.type == "call_expression":
        return extract_callee_name(node)

    return node.text.decode()

SKIP_DIRS = {
    "node_modules", "__pycache__", "venv", "env", "dist", "build", "out",
    "target", "vendor", "third_party", "bower_components", "coverage",
}
MAX_FILE_BYTES = 512 * 1024  # skip generated / minified / data files
PROGRESS_EVERY_SECONDS = 0.5


def _empty_git_info() -> Dict[str, Any]:
    return {"commit_count": 0, "last_modified": None, "recent_commits": []}


def parse_code(
    local_repo_path: str,
    repo_url: str,
    branch: str,
    request_id: str,
    progress_callback: Optional[Callable[[str], None]] = None,
    file_git_index: Optional[Dict[str, Dict[str, Any]]] = None,
):
    """
    Parse code from a locally cloned repository.

    Args:
        local_repo_path: Path to the locally cloned repository
        repo_url: GitHub repository URL
        branch: Branch name
        request_id: Request ID for progress tracking
        progress_callback: Optional callback for progress updates
        file_git_index: Optional {relative_path: git_info} built once from
            `git log` (see git_utils.build_file_git_index). If omitted, git info
            is looked up per file (slow: two subprocesses per file).

    Returns:
        Dictionary with AST and dependency graph
    """
    logger.info(f"parse_code starting for request_id: {request_id}")
    if progress_callback:
        progress_callback("Collecting source code...")

    result = {}
    repo_path = local_repo_path

    source_files = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in SKIP_DIRS]
        for file in files:
            language = detect_file_language(file)
            if not language or language not in LANGUAGE_GRAMMARS:
                continue
            file_path = os.path.join(root, file)
            try:
                if os.path.getsize(file_path) > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            source_files.append((file_path, os.path.relpath(file_path, repo_path), language))

    total = len(source_files)
    logger.info(f"Found {total} source files to parse")
    if progress_callback:
        progress_callback(f"Found {total} source files to parse")

    last_progress = 0.0
    for idx, (file_path, relative_path, language) in enumerate(source_files, 1):
        norm_path = os.path.normpath(relative_path)

        # Each progress update is a Redis write; don't do one per file.
        now = time.monotonic()
        if progress_callback and (now - last_progress >= PROGRESS_EVERY_SECONDS or idx == total):
            progress_callback(f"[{idx}/{total}] Analyzing {norm_path} ({language})...")
            last_progress = now

        parser = get_parser(language)
        node_map = language_node_maps.get(language, {})
        import_types = set(node_map.get('imports', []))
        class_types = set(node_map.get('classes', []))
        function_types = set(node_map.get('functions', []))
        call_types = set(node_map.get('calls', []))

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            code_bytes = code.encode('utf-8')
            tree = parser.parse(code_bytes)

            if file_git_index is not None:
                git_info = file_git_index.get(relative_path.replace(os.sep, "/"), _empty_git_info())
            else:
                try:
                    git_info = get_file_git_info(repo_path, relative_path, branch)
                except Exception as e:
                    logger.warning(f"Could not get git info for {relative_path}: {e}")
                    git_info = _empty_git_info()

            extracted_info = {
                "language": language,
                "imports": [],
                "classes": [],
                "functions": [],
                "git_info": git_info,
                "calls": [],
            }

            # Iterative pre-order walk (recursion overflows on deeply nested files).
            # Each entry carries the enclosing function name so calls are attributed
            # to the right caller.
            stack = [(tree.root_node, None)]
            while stack:
                node, current_function = stack.pop()
                node_type = node.type
                start_line = node.start_point[0] + 1

                if node_type in import_types:
                    extracted_info["imports"].append(
                        extract_import_data(node, code, language, relative_path)
                    )

                if node_type in class_types:
                    name_node = node.child_by_field_name("name")
                    extracted_info["classes"].append({
                        "name": name_node.text.decode() if name_node else f"<anonymous>:Line-{start_line}",
                        "content": code_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='ignore'),
                        "start_line": start_line,
                        "methods": extract_methods(node),
                        "metadata": {"type": node_type, "complexity": calculate_complexity(node)},
                    })

                if node_type in function_types:
                    name_node = node.child_by_field_name("name")
                    current_function = name_node.text.decode() if name_node else f"<anonymous>:Line-{start_line}"
                    extracted_info["functions"].append({
                        "name": current_function,
                        "content": code_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='ignore'),
                        "start_line": start_line,
                        "metadata": {"type": node_type, "complexity": calculate_complexity(node)},
                    })

                if node_type in call_types:
                    extracted_info["calls"].append({
                        "caller": current_function,
                        "callee": extract_callee_name(node),
                        "location": {"line": start_line, "column": node.start_point[1] + 1},
                    })

                # reversed so children are visited in source order
                for child in reversed(node.children):
                    stack.append((child, current_function))

            result[norm_path] = extracted_info

        except Exception as e:
            logger.warning(f"Error processing {norm_path}: {e}")

    if progress_callback:
        progress_callback("Building architecture map...")
    graph = build_dependency_graph(result)
    logger.info(f"parse_code done: {len(result)} files")

    return {
        "ast": result,
        "dependency_graph": graph
    }
