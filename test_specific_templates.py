#!/usr/bin/env python3
import os
import sys
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

# Test specific templates that are most likely to have issues
template_dir = "app/templates"
test_templates = [
    "layout.html",
    "user/dashboard.html",
    "user/analytics.html",
    "user/portfolio.html",
    "user/automation.html",
]

env = Environment(loader=FileSystemLoader(template_dir))

for template_name in test_templates:
    try:
        template = env.get_template(template_name)
        print(f"✓ {template_name} - Valid")
    except TemplateSyntaxError as e:
        print(f"✗ {template_name} - SYNTAX ERROR on line {e.lineno}:")
        print(f"  {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ {template_name} - ERROR: {e}")
        sys.exit(1)

print("All tested templates are valid!")
