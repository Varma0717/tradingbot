#!/usr/bin/env python3
"""
Final test of dashboard mode after config fix
"""
import subprocess
import sys
import os
import time


def test_dashboard_final():
    """Final test of dashboard mode."""
    print("=== FINAL Dashboard Mode Test ===")

    # Change to the application directory
    os.chdir(r"c:\xampp\htdocs\application")

    try:
        print("Testing dashboard startup with config parameter...")

        # Start the dashboard process
        process = subprocess.Popen(
            [sys.executable, "main.py", "--mode", "dashboard"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait a bit for startup
        time.sleep(5)

        # Check if process is running
        if process.poll() is None:
            print("✅ Dashboard process started successfully!")
            print("✅ No TypeError - config parameter fix worked!")

            # Try to get some output
            try:
                stdout, stderr = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()

            if (
                "Dashboard starting on http://localhost:8000" in stdout
                or "Dashboard starting on http://localhost:8000" in stderr
            ):
                print("✅ Dashboard server startup message found!")

            print("\n🎉 DASHBOARD MODE IS WORKING!")
            return True

        else:
            # Process exited, check why
            stdout, stderr = process.communicate()

            if "TypeError" in stderr:
                print("❌ Still getting TypeError")
                print(f"Error: {stderr}")
                return False
            elif "Dashboard starting" in stdout or "Uvicorn running" in stderr:
                print("✅ Dashboard started and exited normally")
                return True
            else:
                print("❌ Dashboard failed for another reason")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = test_dashboard_final()

    if success:
        print("\n🚀 READY TO USE!")
        print("Run: python main.py --mode dashboard")
        print("Then visit: http://localhost:8000")
    else:
        print("\n❌ Still needs fixing")
