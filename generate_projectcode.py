"""generate_projectcode.py

This script walks through the Django project directory, collects the contents of all
text-based source files (Python, HTML, CSS, JavaScript, etc.), and writes them into a
single Markdown file named ``projectcode.md``. Each file's content is wrapped in a
Markdown code block and preceded by a heading that shows the file's relative path.

Binary files (images, archives, SQLite database, etc.) are automatically skipped.
The script also skips the output file itself to avoid recursion.
"""

import os


def is_binary(file_path: str) -> bool:
    """Return True if the file appears to be binary.

    The function attempts to read the file as UTF‑8 text. If a ``UnicodeDecodeError``
    or any other exception occurs, the file is considered binary and will be
    ignored.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            f.read()
        return False
    except Exception:
        return True


def main() -> None:
    # Determine the root directory (the directory containing this script).
    root = os.path.abspath(os.path.dirname(__file__))
    output_path = os.path.join(root, "projectcode.md")

    # File extensions that are definitely binary and should be ignored.
    exclude_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".zip", ".sqlite", ".db"}

    # Open the output file for writing (this will truncate any existing content).
    with open(output_path, "w", encoding="utf-8") as out:
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                # Skip known binary extensions.
                if ext in exclude_exts:
                    continue

                file_path = os.path.join(dirpath, filename)

                # Skip the output file itself to avoid infinite recursion.
                if os.path.abspath(file_path) == os.path.abspath(output_path):
                    continue

                # Skip files that cannot be read as text.
                if is_binary(file_path):
                    continue

                # Compute the relative path for heading.
                rel_path = os.path.relpath(file_path, root)

                # Exclude static/dashboard and static/bootstrap directories.
                # This check works for any depth under the project root.
                if rel_path.startswith(os.path.join("static", "dashboard")) or rel_path.startswith(os.path.join("static", "bootstrap")) or rel_path.startswith(os.path.join(".git")):
                    continue

                # Write a heading with the relative path and then the file content.
                out.write(f"## {rel_path}\n")
                out.write("```\n")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        out.write(f.read())
                except Exception as e:
                    out.write(f"[Error reading file: {e}]")
                out.write("\n```\n\n")


if __name__ == "__main__":
    main()
