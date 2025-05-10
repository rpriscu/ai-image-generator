"""
Python 3.13 Compatibility Script

This script helps to downgrade packages to versions that work better with Python 3.13.
It's recommended to run this script if you're using Python 3.13 for local development.
"""
import subprocess
import sys
import os

# Packages that need to be downgraded for Python 3.13 compatibility
PACKAGES_TO_DOWNGRADE = {
    'Flask-Session': '0.4.0',
    'Werkzeug': '2.3.7',
    'Flask': '2.3.3',
    'itsdangerous': '2.1.2',
    'jinja2': '3.1.2'
}

def downgrade_packages():
    """Downgrade packages to versions that are compatible with Python 3.13"""
    print(f"Python version: {sys.version}")
    print("Downgrading packages for Python 3.13 compatibility...")
    
    for package, version in PACKAGES_TO_DOWNGRADE.items():
        print(f"Downgrading {package} to version {version}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                f"{package}=={version}", "--force-reinstall"
            ])
            print(f"Successfully downgraded {package} to version {version}")
        except subprocess.CalledProcessError as e:
            print(f"Error downgrading {package}: {e}")
    
    print("\nAll packages have been downgraded for Python 3.13 compatibility.")
    print("You should now be able to run the application without any errors.")
    print("\nTo run the application, use: python run.py")

def update_requirements():
    """Update requirements.txt with the downgraded package versions"""
    try:
        # Read the current requirements file
        with open('requirements.txt', 'r') as f:
            requirements = f.readlines()
        
        # Update the versions
        new_requirements = []
        for line in requirements:
            package = line.split('==')[0].strip()
            if package in PACKAGES_TO_DOWNGRADE:
                new_requirements.append(f"{package}=={PACKAGES_TO_DOWNGRADE[package]}\n")
            else:
                new_requirements.append(line)
        
        # Write the updated requirements file
        with open('requirements.txt', 'w') as f:
            f.writelines(new_requirements)
        
        print("Updated requirements.txt with compatible package versions.")
    except Exception as e:
        print(f"Error updating requirements.txt: {e}")

if __name__ == "__main__":
    if sys.version_info.major == 3 and sys.version_info.minor == 13:
        downgrade_packages()
        update_requirements()
    else:
        print(f"This script is intended for Python 3.13, but you're using {sys.version}")
        print("Only run this if you're using Python 3.13 for local development.")
        choice = input("Continue anyway? (y/n): ")
        if choice.lower() == 'y':
            downgrade_packages()
            update_requirements() 