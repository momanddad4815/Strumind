import os
import re

def fix_imports(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Replace imports
                modified_content = re.sub(r'from backend\.', 'from ', content)
                
                if content != modified_content:
                    with open(file_path, 'w') as f:
                        f.write(modified_content)
                    print(f"Fixed imports in {file_path}")

if __name__ == "__main__":
    fix_imports('/workspace/Strumind/backend')