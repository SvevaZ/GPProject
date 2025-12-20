"""
Script to execute the tests with coverage report
Run from main project GPProject/:
    python TESTS/run_coverage.py

Coverage Report: 78%
"""

import subprocess
import sys
import os

print("=" * 70)
print("ZIPRA - Test Coverage Report")
print("=" * 70)
print()

# Verify TESTS structure
if not os.path.exists("tests"):
    print(" Folder 'tests' not found!")
    print("   Execute this script from main project root (GPProject/)")
    sys.exit(1)

if not os.path.exists("tests/__init__.py"):
    print("  File tests/__init__.py not found. Creating ...")
    with open("tests/__init__.py", "w") as f:
        pass
    print("✓ File tests/__init__.py created")

if not os.path.exists("tests/test.py"):
    print(" File tests/test.py not found!")
    sys.exit(1)

print("✓ Correct file structure")
print()

# Check if coverage is installed
try:
    import coverage
    print("✓ Coverage module found")
except ImportError:
    print(" Installing coverage...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "coverage"])
    print("✓ Coverage installed")

print()
print("=" * 70)
print("Running Tests...")
print("=" * 70)
print()

# Run tests with coverage - using discover
cmd = [
    sys.executable,
    "-m", "coverage", "run",
    "--omit=tests/*",
    "-m", "unittest", "discover",
    "-s", "tests",
    "-p", "test.py",
    "-v"
]

result = subprocess.run(cmd)

if result.returncode != 0:
    print("\n Some tests failed!")
    print("\nPossible issues:")
    print("  - Missing test data in ./DATA/ folder")
    print("  - ZIPRA.py not found or has errors")
    print("  - Function names mismatch (check Mask_tiff, Barplot_classes)")

print()
print("=" * 70)
print("Coverage Report")
print("=" * 70)
print()

# Show terminal report
subprocess.run([sys.executable, "-m", "coverage", "report", "-m"])

# Generate HTML report
print()
print("Generating HTML report...")
subprocess.run([sys.executable, "-m", "coverage", "html"])

print()
print("=" * 70)
print("Tests completed successfully!")
print("=" * 70)
print()
print("HTML coverage report: htmlcov/index.html")


# Try to open automatically

import webbrowser
import os.path

manually = False # Flag to indicate if manual instructions are needed

report_path = os.path.join(os.getcwd(), "htmlcov", "index.html")

if os.path.exists(report_path):
    print("Opening coverage report in browser...")

    try:
        if sys.platform.startswith("win"):  # ✅ Windows
            url = "file:///" + report_path.replace("\\", "/")

            browsers = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files\Mozilla Firefox\firefox.exe"]

            opened = False

            for path in browsers:
                if os.path.exists(path):
                    try:
                        webbrowser.get(f'"{path}" %s').open(url)
                        print(f"Opened with: {path}")
                        opened = True
                        break
                    except Exception as e:
                        pass

            if not opened:
                print("Could not open automatically.")
                print("Open manually:", url)


        elif sys.platform == "darwin":
            webbrowser.open_new_tab(url)   # ✅ macOS
        else:
            webbrowser.open_new_tab(url)   # ✅ Linux

    except Exception as e:
        print(f"Error opening browser: {e}")
        print("Open manually:", report_path)
        manually = True
else:
    print("Coverage HTML report not found. Generate it first.")

# Instructions to open manually
if manually:
    print()
    print("To view manually:")
    print("  macOS:   open htmlcov/index.html")
    print("  Linux:   xdg-open htmlcov/index.html")
    print(f" Windows (cmd.exe): start <browser_name> \"{report_path}\"")
    print("           Examples: start chrome ..., start msedge ..., start firefox ...")
    print()