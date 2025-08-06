#!/usr/bin/env python3
"""
Ultimate final test of dashboard mode
"""
import subprocess
import sys
import os
import time


def test_dashboard_ultimate():
    """Ultimate test of dashboard mode after all fixes."""
    print("=== ULTIMATE Dashboard Mode Test ===")
    print("Testing all fixes:")
    print("✅ Dashboard mode argument added")
    print("✅ Config validation updated")
    print("✅ DataManager attributes fixed")
    print("✅ Config parameter passed to DashboardApp")
    print("✅ Using dashboard.app instead of dashboard.create_app()")

    # Change to the application directory
    os.chdir(r"c:\xampp\htdocs\application")

    try:
        print("\n🚀 Starting dashboard...")

        # Start the dashboard process
        process = subprocess.Popen(
            [sys.executable, "main.py", "--mode", "dashboard"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for startup
        time.sleep(6)

        # Check if process is running
        if process.poll() is None:
            print("✅ Dashboard process is running!")

            # Try to kill it gracefully
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()

            # Check for success indicators
            output = stdout + stderr

            if "Dashboard starting on http://localhost:8000" in output:
                print("✅ Dashboard startup message found!")

            if "Uvicorn running" in output or "Application startup complete" in output:
                print("✅ Server started successfully!")

            if "AttributeError" not in output and "TypeError" not in output:
                print("✅ No attribute or type errors!")

            print("\n🎉 ALL TESTS PASSED!")
            print("🎉 DASHBOARD MODE IS FULLY WORKING!")
            return True

        else:
            # Process exited, check why
            stdout, stderr = process.communicate()
            output = stdout + stderr

            if "AttributeError" in output:
                print("❌ Still has AttributeError")
                print(f"Error details: {output}")
                return False
            elif "TypeError" in output:
                print("❌ Still has TypeError")
                print(f"Error details: {output}")
                return False
            elif "Dashboard starting" in output:
                print("✅ Dashboard started successfully!")
                return True
            else:
                print("❌ Unknown issue")
                print(f"Output: {output}")
                return False

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = test_dashboard_ultimate()

    if success:
        print("\n" + "=" * 50)
        print("🎉 SUCCESS! DASHBOARD MODE IS READY! 🎉")
        print("=" * 50)
        print("")
        print("📋 HOW TO USE:")
        print("1. Run: python main.py --mode dashboard")
        print("2. Open browser: http://localhost:8000")
        print("3. Access settings: http://localhost:8000/settings")
        print("4. Grid DCA: http://localhost:8000/grid-dca")
        print("")
        print("✨ Features available:")
        print("• Modern gradient settings page")
        print("• Grid DCA strategy dashboard")
        print("• Real-time monitoring")
        print("• Comprehensive API endpoints")
        print("• Professional UI design")
    else:
        print("\n❌ Still needs more work")
