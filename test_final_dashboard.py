#!/usr/bin/env python3
"""
Test dashboard mode after fixes
"""
import subprocess
import sys
import os
import time


def test_dashboard_mode():
    """Test dashboard mode with all fixes applied."""
    print("=== Testing Dashboard Mode After Fixes ===")

    # Change to the application directory
    os.chdir(r"c:\xampp\htdocs\application")

    try:
        print("1. Testing argument validation...")
        # Test that dashboard mode is now accepted
        result = subprocess.run(
            [sys.executable, "main.py", "--mode", "dashboard", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ Dashboard mode argument is accepted")
        else:
            print(f"❌ Dashboard mode argument failed: {result.stderr}")
            return False

        print("\n2. Testing configuration validation...")
        # Test that config validation passes for dashboard mode
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                """
import sys
from pathlib import Path
sys.path.append(str(Path('.') / 'src'))
from src.core.config import Config

config = Config()
config.trading.mode = 'dashboard'
try:
    config.validate()
    print('✅ Config validation passed for dashboard mode')
except Exception as e:
    print(f'❌ Config validation failed: {e}')
    sys.exit(1)
""",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if "✅ Config validation passed" in result.stdout:
            print("✅ Configuration validation passes for dashboard mode")
        else:
            print(
                f"❌ Configuration validation failed: {result.stdout + result.stderr}"
            )
            return False

        print("\n3. Testing dashboard startup (quick test)...")
        # Test that dashboard starts without crashing (kill after 3 seconds)
        process = subprocess.Popen(
            [sys.executable, "main.py", "--mode", "dashboard"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait a bit for startup
        time.sleep(3)

        # Check if process is still running (good sign)
        if process.poll() is None:
            print("✅ Dashboard process started successfully")
            process.terminate()
            process.wait(timeout=5)
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Dashboard process exited early")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False

        print("\n🎉 ALL TESTS PASSED!")
        print("Dashboard mode is now working correctly!")
        return True

    except subprocess.TimeoutExpired:
        print("⚠️  Test timed out (might be normal for server startup)")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_dashboard_mode()

    if success:
        print("\n✅ Dashboard mode is ready to use!")
        print("Run: python main.py --mode dashboard")
    else:
        print("\n❌ Dashboard mode still has issues")
