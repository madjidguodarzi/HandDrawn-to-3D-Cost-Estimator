import os
import ast
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime

# ----------------------------
# تنظیمات فیلتر فایل‌ها
# ----------------------------

EXCLUDE_NAMES = {
    '__pycache__', 'venv', '.venv', 'env', 'Lib', 
    'bin', 'Scripts', 'include', 'lib', 'lib64', 'etc', 'share',
    '.git', '.idea', '.vscode', 'node_modules', 'build', 'dist',
    'backup', 'model'  # مهم: فولدر backup را حذف کن
}

INCLUDE_EXTENSIONS = {
    '.py', '.html', '.js', '.css'
}

ADDITIONAL_INCLUDE_FILES = {
    'requirements.txt', 'pyproject.toml', 'setup.py', 'Dockerfile', 'README.md'
}

def should_include(path):
    """آیا فایل/فولدر باید در struct و بکاپ گنجانده شود؟"""
    name = path.name

    if name in EXCLUDE_NAMES:
        return False

    if path.is_file():
        if name.startswith('.') and name not in {'.env', '.gitignore'}:
            return False
        if path.suffix not in INCLUDE_EXTENSIONS and name not in ADDITIONAL_INCLUDE_FILES:
            return False

    return True


# ----------------------------
# تولید structure.txt
# ----------------------------

def generate_structure(output_file="others/source/structure.txt"):
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / output_file

    class CodeVisitor(ast.NodeVisitor):
        def __init__(self):
            self.items = []

        def visit_FunctionDef(self, node):
            args = [arg.arg for arg in node.args.args if isinstance(arg, ast.arg)]
            args_str = ", ".join(args)
            self.items.append(f"def {node.name}({args_str}):")

        def visit_AsyncFunctionDef(self, node):
            args = [arg.arg for arg in node.args.args if isinstance(arg, ast.arg)]
            args_str = ", ".join(args)
            self.items.append(f"async def {node.name}({args_str}):")

        def visit_ClassDef(self, node):
            bases = [b.id if isinstance(b, ast.Name) else str(b) for b in node.bases]
            bases_str = f"({', '.join(bases)})" if bases else ""
            self.items.append(f"class {node.name}{bases_str}:")
            method_visitor = CodeVisitor()
            method_visitor.generic_visit(node)
            self.items.extend([f"    {item}" for item in method_visitor.items])

    def get_code_structure(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read())
                except SyntaxError:
                    return ["# [Syntax Error]"]
            visitor = CodeVisitor()
            visitor.visit(tree)
            return visitor.items
        except Exception:
            return ["# [Error reading file]"]

    def walk_tree(path, prefix="", is_last=False):
        if not should_include(path):
            return

        # Connector برای آیتم فعلی
        connector = "└── " if is_last else "├── "
        yield f"{prefix}{connector}{path.name}"

        if path.is_dir():
            children = sorted(filter(should_include, path.iterdir()), key=lambda x: (x.is_file(), x.name))
            if not children:
                return

            # زیرشاخه‌ها
            for i, child in enumerate(children):
                is_last_child = (i == len(children) - 1)
                # ادامه خط عمودی اگر فولدر فعلی آخرین فرزند نباشد
                extension = "    " if is_last else "│   "
                yield from walk_tree(child, prefix + extension, is_last_child)

        elif path.suffix == ".py":
            code_items = get_code_structure(path)
            if code_items:
                # ادامه prefix با خط عمودی اگر فایل فعلی آخرین فایل نباشد
                extension = "    " if is_last else "│   "
                func_prefix = prefix + extension
                for j, item in enumerate(code_items):
                    is_last_item = (j == len(code_items) - 1)
                    item_connector = "└── " if is_last_item else "├── "
                    yield f"{func_prefix}{item_connector}{item}"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"{project_root.name}/\n")
        children = sorted(filter(should_include, project_root.iterdir()), key=lambda x: (x.is_file(), x.name))
        for i, child in enumerate(children):
            is_last = (i == len(children) - 1)
            for line in walk_tree(child, "", is_last):
                f.write(line + "\n")

    print(f"✅ Structure file generated: {output_path}")
    return output_path


# ----------------------------
# ذخیره سورس فایل‌ها در sources.json
# ----------------------------

def save_sources_to_json(output_file="others/source/out.json"):
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / output_file
    sources = {}

    def collect_files(path, relative_path=""):
        if not should_include(path):
            return

        # if path.is_file() and (path.suffix == ".py"):
        if path.is_file() and (path.suffix in INCLUDE_EXTENSIONS):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                # استفاده از مسیر نسبی با جداکننده `/` (حتی در ویندوز)
                key = path.as_posix()
                sources[key] = content
            except Exception as e:
                try:
                    # اگر فایل باینری باشد (مثلاً برای ذخیره سازی یا پردازش خاص)
                    with open(path, "rb") as f:
                        content = f.read()  # محتوا به صورت bytes خواهد بود
                    sources[key] = content
                except Exception as e:
                    print(f"⚠️ نمی‌توان فایل را خواند {path}: {e}")

        elif path.is_dir():
            for item in path.iterdir():
                if should_include(item):
                    new_relative = Path(relative_path) / item.name
                    collect_files(item, new_relative)

    for item in project_root.iterdir():
        if should_include(item):
            collect_files(item, item.name)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)

    print(f"✅ Sources saved to JSON: {output_path}")
    return output_path


# ----------------------------
# ایجاد فایل 7z بکاپ
# ----------------------------

def create_backup():
    project_root = Path(__file__).parent.parent.parent
    backup_folder = project_root / "backup"
    backup_folder.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"backup-{timestamp}.7z"
    backup_path = backup_folder / backup_filename

    # اول structure.txt و sources.json را بسازیم
    generate_structure()
    save_sources_to_json()

    # لیست تمام فایل‌ها و فولدرهایی که باید بکاپ بگیریم
    temp_dir = project_root / f".temp_backup_{timestamp}"
    temp_dir.mkdir()

    try:
        # کپی فایل‌های مجاز به temp_dir
        for item in project_root.iterdir():
            if not should_include(item):
                continue
            dest = temp_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, ignore=shutil.ignore_patterns('*__pycache__*', '*.pyc'))
            else:
                shutil.copy2(item, dest)

        # فراخوانی 7z برای فشرده‌سازی
        print(f"در حال فشرده‌سازی: {backup_path}")
        result = subprocess.run([
            '7z', 'a',
            '-t7z',
            '-m0=lzma',
            '-mx=9',      # حداکثر فشردگی
            '-mfb=64',
            '-md=32m',
            '-ms=on',     # solid mode
            str(backup_path),
            f'{temp_dir}/*'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ بکاپ با موفقیت ایجاد شد: {backup_path}")
        else:
            print("❌ خطا در اجرای 7z:")
            print(result.stderr)

    except Exception as e:
        print(f"❌ خطای هنگام بکاپ: {e}")
    finally:
        # پاک کردن temp
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


# ----------------------------
# اجرای اصلی
# ----------------------------

if __name__ == "__main__":
    create_backup()
