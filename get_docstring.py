import os
import ast

def extract_docstrings_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=file_path)

    docstrings = []

    # Docstring module
    module_docstring = ast.get_docstring(tree)
    if module_docstring:
        docstrings.append((file_path, "module", None, module_docstring))

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            doc = ast.get_docstring(node)
            if doc:
                docstrings.append((file_path, "function", node.name, doc))
        elif isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node)
            if doc:
                docstrings.append((file_path, "class", node.name, doc))

    return docstrings

def extract_from_project(root_folder):
    all_docstrings = []
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    docstrings = extract_docstrings_from_file(file_path)
                    all_docstrings.extend(docstrings)
                except Exception as e:
                    print(f"Lỗi khi xử lý {file_path}: {e}")
    return all_docstrings

if __name__ == "__main__":
    # Đổi '.' thành đường dẫn gốc dự án của bạn nếu cần
    project_path = "."
    docstrings = extract_from_project(project_path)

    for file_path, kind, name, doc in docstrings:
        print("="*60)
        print(f"File: {file_path}")
        print(f"Loại: {kind}")
        if name:
            print(f"Tên: {name}")
        print("Docstring:")
        print(doc)
