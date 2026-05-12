import ast

def clean_source_code(source):
    cleaned_lines = []

    for line in source.splitlines():
        stripped = line.strip()

        if stripped.startswith("!"):
            continue
        if stripped.startswith("%"):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)

def parse_python_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    source = clean_source_code(source)
    tree = ast.parse(source)

    functions = []
    classes = []
    imports = []

    class CodeVisitor(ast.NodeVisitor):
        def visit_Import(self, node):
            for alias in node.names:
                imports.append(alias.name)
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            if node.module:
                imports.append(node.module)
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            classes.append({
                "name": node.name,
                "line": node.lineno
            })
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            calls = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        calls.append(child.func.id)
                    elif isinstance(child.func, ast.Attribute):
                        calls.append(child.func.attr)

            docstring = ast.get_docstring(node)

            functions.append({
                "name": node.name,
                "args": [arg.arg for arg in node.args.args],
                "calls": calls,
                "docstring": docstring,
                "line": node.lineno
            })

            self.generic_visit(node)

    visitor = CodeVisitor()
    visitor.visit(tree)

    return {
        "functions": functions,
        "classes": classes,
        "imports": imports
    }