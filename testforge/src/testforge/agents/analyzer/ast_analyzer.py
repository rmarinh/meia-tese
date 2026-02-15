"""Tree-sitter based AST analysis for Python test files."""

from __future__ import annotations

import re
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

from testforge.models.style_guide import (
    AssertionPattern,
    FixturePattern,
    GoldenExample,
    ImportPattern,
    TestFunctionPattern,
)

PY_LANGUAGE = Language(tspython.language())


def _get_parser() -> Parser:
    parser = Parser(PY_LANGUAGE)
    return parser


def _node_text(node, source_bytes: bytes) -> str:
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8")


def parse_python_file(source_code: str, file_path: str = "<unknown>") -> GoldenExample:
    """Parse a Python test file into a GoldenExample using Tree-sitter."""
    parser = _get_parser()
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)
    root = tree.root_node

    imports = _extract_imports(root, source_bytes)
    fixtures = _extract_fixtures(root, source_bytes)
    test_functions = _extract_test_functions(root, source_bytes)
    helper_functions = _extract_helper_functions(root, source_bytes)
    class_names = _extract_class_names(root, source_bytes)

    return GoldenExample(
        file_path=file_path,
        source_code=source_code,
        imports=imports,
        fixtures=fixtures,
        test_functions=test_functions,
        helper_functions=helper_functions,
        class_names=class_names,
    )


def _extract_imports(root, source_bytes: bytes) -> list[ImportPattern]:
    imports = []
    for node in root.children:
        if node.type == "import_statement":
            text = _node_text(node, source_bytes)
            match = re.match(r"import\s+([\w.]+)(?:\s+as\s+(\w+))?", text)
            if match:
                imports.append(
                    ImportPattern(
                        module=match.group(1),
                        alias=match.group(2),
                        is_from_import=False,
                    )
                )
        elif node.type == "import_from_statement":
            text = _node_text(node, source_bytes)
            match = re.match(r"from\s+([\w.]+)\s+import\s+(.+)", text)
            if match:
                module = match.group(1)
                names_str = match.group(2).strip()
                names = [n.strip() for n in names_str.split(",")]
                imports.append(
                    ImportPattern(
                        module=module,
                        names=names,
                        is_from_import=True,
                    )
                )
    return imports


def _extract_fixtures(root, source_bytes: bytes) -> list[FixturePattern]:
    fixtures = []
    for node in root.children:
        if node.type == "decorated_definition":
            decorators = []
            func_node = None
            for child in node.children:
                if child.type == "decorator":
                    decorators.append(_node_text(child, source_bytes))
                elif child.type == "function_definition":
                    func_node = child

            if func_node and any("fixture" in d for d in decorators):
                name = ""
                for child in func_node.children:
                    if child.type == "identifier":
                        name = _node_text(child, source_bytes)
                        break

                scope = "function"
                for d in decorators:
                    scope_match = re.search(r'scope=["\'](\w+)["\']', d)
                    if scope_match:
                        scope = scope_match.group(1)

                body = _node_text(func_node, source_bytes)
                yields = "yield" in body

                docstring = _extract_docstring(func_node, source_bytes)

                fixtures.append(
                    FixturePattern(
                        name=name,
                        scope=scope,
                        yields=yields,
                        docstring=docstring,
                        body_summary=_summarize_body(func_node, source_bytes),
                    )
                )
    return fixtures


def _extract_test_functions(root, source_bytes: bytes) -> list[TestFunctionPattern]:
    functions = []

    for node in _iter_function_defs(root):
        name = ""
        for child in node.children:
            if child.type == "identifier":
                name = _node_text(child, source_bytes)
                break

        if not name.startswith("test_"):
            continue

        decorators = _get_decorators(node, source_bytes)
        fixtures_used = _get_parameters(node, source_bytes)
        assertions = _extract_assertions(node, source_bytes)
        docstring = _extract_docstring(node, source_bytes)

        http_method = None
        endpoint = None
        body_text = _node_text(node, source_bytes)
        for method in ("get", "post", "put", "patch", "delete", "head", "options"):
            pattern = rf"\.{method}\s*\("
            if re.search(pattern, body_text):
                http_method = method.upper()
                # Try quoted string first, then f-string
                url_match = re.search(rf'\.{method}\s*\(\s*["\']([^"\']+)["\']', body_text)
                if url_match:
                    endpoint = url_match.group(1)
                else:
                    # Match f-string patterns like f"{base_url}/api/users"
                    fstr_match = re.search(
                        rf'\.{method}\s*\(\s*f["\'][^"\']*\}}(/[^"\']*)["\']',
                        body_text,
                    )
                    if fstr_match:
                        endpoint = fstr_match.group(1)
                break

        line_count = node.end_point[0] - node.start_point[0] + 1

        functions.append(
            TestFunctionPattern(
                name=name,
                docstring=docstring,
                decorators=decorators,
                fixtures_used=fixtures_used,
                http_method=http_method,
                endpoint=endpoint,
                assertions=assertions,
                body_summary=_summarize_body(node, source_bytes),
                line_count=line_count,
            )
        )

    return functions


def _iter_function_defs(node):
    """Yield all function_definition nodes including inside decorated_definitions."""
    for child in node.children:
        if child.type == "function_definition":
            yield child
        elif child.type == "decorated_definition":
            for sub in child.children:
                if sub.type == "function_definition":
                    yield sub
        elif child.type == "class_definition":
            body = None
            for sub in child.children:
                if sub.type == "block":
                    body = sub
                    break
            if body:
                yield from _iter_function_defs(body)


def _extract_helper_functions(root, source_bytes: bytes) -> list[str]:
    helpers = []
    for node in root.children:
        func_node = None
        if node.type == "function_definition":
            func_node = node
        elif node.type == "decorated_definition":
            is_fixture = False
            for child in node.children:
                if child.type == "decorator" and "fixture" in _node_text(child, source_bytes):
                    is_fixture = True
                elif child.type == "function_definition":
                    func_node = child
            if is_fixture:
                continue

        if func_node:
            name = ""
            for child in func_node.children:
                if child.type == "identifier":
                    name = _node_text(child, source_bytes)
                    break
            if name and not name.startswith("test_"):
                helpers.append(name)
    return helpers


def _extract_class_names(root, source_bytes: bytes) -> list[str]:
    classes = []
    for node in root.children:
        if node.type == "class_definition":
            for child in node.children:
                if child.type == "identifier":
                    classes.append(_node_text(child, source_bytes))
                    break
    return classes


def _get_decorators(node, source_bytes: bytes) -> list[str]:
    """Get decorators for a function that may be inside a decorated_definition."""
    parent = node.parent
    if parent and parent.type == "decorated_definition":
        return [
            _node_text(child, source_bytes).lstrip("@")
            for child in parent.children
            if child.type == "decorator"
        ]
    return []


def _get_parameters(node, source_bytes: bytes) -> list[str]:
    for child in node.children:
        if child.type == "parameters":
            params = []
            for param in child.children:
                if param.type == "identifier":
                    name = _node_text(param, source_bytes)
                    if name != "self":
                        params.append(name)
            return params
    return []


def _extract_assertions(node, source_bytes: bytes) -> list[AssertionPattern]:
    assertions = []
    body_text = _node_text(node, source_bytes)

    for line in body_text.split("\n"):
        line = line.strip()
        if line.startswith("assert "):
            assertions.append(AssertionPattern(style="assert", pattern=line))
        elif "pytest.raises" in line:
            assertions.append(AssertionPattern(style="pytest.raises", pattern=line))
        elif re.match(r"self\.assert\w+", line):
            assertions.append(AssertionPattern(style="assertEqual", pattern=line))

    return assertions


def _extract_docstring(node, source_bytes: bytes) -> str | None:
    for child in node.children:
        if child.type == "block":
            for stmt in child.children:
                if stmt.type == "expression_statement":
                    for expr in stmt.children:
                        if expr.type == "string":
                            text = _node_text(expr, source_bytes)
                            return text.strip("\"'").strip()
            break
    return None


def _summarize_body(node, source_bytes: bytes) -> str:
    """Create a brief summary of the function body."""
    text = _node_text(node, source_bytes)
    lines = text.split("\n")
    if len(lines) <= 10:
        return text
    return "\n".join(lines[:10]) + f"\n... ({len(lines) - 10} more lines)"


def parse_golden_files(file_paths: list[str | Path]) -> list[GoldenExample]:
    """Parse multiple golden test files."""
    examples = []
    for path in file_paths:
        path = Path(path)
        if path.exists() and path.suffix == ".py":
            source = path.read_text(encoding="utf-8")
            examples.append(parse_python_file(source, str(path)))
    return examples
