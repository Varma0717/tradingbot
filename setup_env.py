#!/usr/bin/env python3
"""
Setup script for Crypto Trading Bot environment
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, check=True, shell=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            command, shell=shell, check=check, capture_output=True, text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def main():
    print("🚀 Setting up Crypto Trading Bot environment...")
    print("=" * 50)

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    print(f"📁 Working directory: {project_dir}")

    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required")
        print(f"   Current version: {sys.version}")
        return False

    print(f"✅ Python version: {sys.version.split()[0]}")

    # Setup virtual environment
    venv_path = project_dir / "venv"

    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        success, stdout, stderr = run_command([sys.executable, "-m", "venv", "venv"])
        if not success:
            print(f"❌ Failed to create virtual environment: {stderr}")
            return False
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")

    # Activate virtual environment
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"

    if not python_exe.exists():
        print("❌ Virtual environment Python not found")
        return False

    # Upgrade pip
    print("📦 Upgrading pip...")
    success, stdout, stderr = run_command(
        [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"]
    )
    if not success:
        print(f"⚠️  Warning: Failed to upgrade pip: {stderr}")
    else:
        print("✅ Pip upgraded")

    # Install wheel and setuptools
    print("📦 Installing build tools...")
    success, stdout, stderr = run_command(
        [str(pip_exe), "install", "wheel", "setuptools"]
    )
    if not success:
        print(f"❌ Failed to install build tools: {stderr}")
        return False
    print("✅ Build tools installed")

    # Install requirements
    requirements_file = project_dir / "requirements.txt"
    if requirements_file.exists():
        print("📦 Installing project requirements...")
        success, stdout, stderr = run_command(
            [str(pip_exe), "install", "-r", str(requirements_file)]
        )
        if not success:
            print(f"❌ Failed to install requirements: {stderr}")
            print("💡 You may need to install some packages manually")
            print("   Common issues:")
            print(
                "   - TA-Lib: Download from https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib"
            )
            print("   - Microsoft Visual C++ Build Tools may be required")
            return False
        print("✅ Requirements installed")
    else:
        print("⚠️  No requirements.txt found")

    # Create .env file
    env_file = project_dir / ".env"
    env_example = project_dir / ".env.example"

    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        shutil.copy(env_example, env_file)
        print("✅ .env file created")

    # Test critical imports
    print("🧪 Testing critical imports...")
    test_imports = [
        "ccxt",
        "pandas",
        "numpy",
        "fastapi",
        "sqlalchemy",
        "yaml",
        "dotenv",
    ]

    failed_imports = []
    for module in test_imports:
        success, stdout, stderr = run_command(
            [str(python_exe), "-c", f"import {module}"]
        )
        if success:
            print(f"  ✅ {module}")
        else:
            print(f"  ❌ {module} - {stderr.strip()}")
            failed_imports.append(module)

    if failed_imports:
        print(f"\n⚠️  Some imports failed: {', '.join(failed_imports)}")
        print("   The bot may not work correctly until these are resolved.")
    else:
        print("\n🎉 All critical packages imported successfully!")

    # Final instructions
    print("\n" + "=" * 50)
    print("🎊 Environment setup completed!")
    print("=" * 50)
    print("\n📋 Next steps:")

    if sys.platform == "win32":
        print("   1. Activate environment: venv\\Scripts\\activate.bat")
    else:
        print("   1. Activate environment: source venv/bin/activate")

    print("   2. Configure .env file with your settings")
    print("   3. Start dashboard: python run_dashboard.py")
    print("   4. Start main bot: python main.py")
    print("\n📖 Check README.md for detailed setup instructions")

    return len(failed_imports) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
