#!/usr/bin/env python3
"""
Simple script to test Jinja2 template compilation and identify syntax errors.
"""

import os
import sys
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError


def test_templates():
    """Test all HTML templates for syntax errors."""

    template_dir = os.path.join(os.path.dirname(__file__), "app", "templates")

    if not os.path.exists(template_dir):
        print(f"Template directory not found: {template_dir}")
        return False

    env = Environment(loader=FileSystemLoader(template_dir))

    errors_found = False

    # Get all HTML files recursively
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith(".html"):
                # Get relative path from template directory
                rel_path = os.path.relpath(os.path.join(root, file), template_dir)
                template_name = rel_path.replace(os.path.sep, "/")

                try:
                    # Try to parse the template
                    template = env.get_template(template_name)
                    print(f"✓ {template_name} - OK")
                except TemplateSyntaxError as e:
                    print(f"✗ {template_name} - SYNTAX ERROR:")
                    print(f"  Line {e.lineno}: {e.message}")
                    if hasattr(e, "source"):
                        # Show context around the error
                        lines = e.source.split("\n")
                        start = max(0, e.lineno - 3)
                        end = min(len(lines), e.lineno + 2)
                        for i in range(start, end):
                            marker = " >>> " if i + 1 == e.lineno else "     "
                            print(f"{marker}{i+1:4}: {lines[i]}")
                    print()
                    errors_found = True
                except Exception as e:
                    print(f"✗ {template_name} - OTHER ERROR: {e}")
                    errors_found = True

    return not errors_found


if __name__ == "__main__":
    print("Testing Jinja2 templates...")
    success = test_templates()
    if success:
        print("\nAll templates are valid!")
        sys.exit(0)
    else:
        print("\nTemplate errors found!")
        sys.exit(1)
