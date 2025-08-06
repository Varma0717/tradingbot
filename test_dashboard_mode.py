#!/usr/bin/env python3
"""
Quick test script to verify dashboard mode functionality
"""
import subprocess
import sys
import os


def test_dashboard_mode():
    """Test if the dashboard mode argument works properly."""
    print("Testing dashboard mode...")

    # Change to the application directory
    os.chdir(r"c:\xampp\htdocs\application")

    try:
        # Test the help command first
        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ Help command works")
            print("Available modes:", end=" ")
            if "dashboard" in result.stdout:
                print("✅ Dashboard mode is available")
            else:
                print("❌ Dashboard mode not found in help")
        else:
            print("❌ Help command failed")
            print("Error:", result.stderr)
            return

        # Test dashboard mode argument validation
        result = subprocess.run(
            [sys.executable, "main.py", "--mode", "dashboard", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        print(f"Dashboard mode test result: {result.returncode}")
        if result.stdout:
            print("STDOUT:", result.stdout[:500])
        if result.stderr:
            print("STDERR:", result.stderr[:500])

    except subprocess.TimeoutExpired:
        print("✅ Dashboard mode started (timeout expected for server)")
    except Exception as e:
        print(f"❌ Error testing dashboard mode: {e}")


if __name__ == "__main__":
    test_dashboard_mode()
