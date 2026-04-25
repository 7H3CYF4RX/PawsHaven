import os
import ast
import sys

def get_imports(path):
    imports = set()
    for root, dirs, files in os.walk(path):
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for n in node.names:
                                imports.add(n.name.split('.')[0])
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports.add(node.module.split('.')[0])
                except Exception as e:
                    pass
    return imports

# Use a basic list of stdlib if sys.stdlib_module_names is not available
if hasattr(sys, 'stdlib_module_names'):
    stdlib = sys.stdlib_module_names
else:
    from distutils.sysconfig import get_python_lib
    stdlib = set()
    # It's an approximation for older Pythons, but let's hope it's 3.10+

all_imports = get_imports('.')
third_party = {imp for imp in all_imports if imp not in stdlib and imp != ''}

local_modules = {'app', 'blueprints', 'config', 'middleware', 'utils', 'internal_services', 'routes'}
third_party = third_party - local_modules

print("Third party imports found in code:")
for imp in sorted(list(third_party)):
    print(imp)

with open('requirements.txt', 'r') as f:
    reqs = f.read().splitlines()
    
print("\nRequirements in requirements.txt:")
for req in reqs:
    print(req)
