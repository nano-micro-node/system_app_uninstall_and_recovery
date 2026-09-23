# system_app_uninstall_and_recovery
Fast, lightweight command-line tool to safely debloat, uninstall, and restore Android system apps via ADB. Requires no root and no unlocked bootloader

📱 Android ADB System App Manager & Debloater
A clean, safe Python-based CLI tool (buildable into a standalone .exe) designed to help you remove unwanted pre-installed system apps (bloatware) and recover previously deleted apps on any Android device.

It utilizes Android's native pm uninstall -k --user 0 and cmd package install-existing commands, meaning it works without root privileges and without unlocking your bootloader.

⚡ Key Features
No Root Required: Operates entirely through user-space ADB commands (--user 0).

Safe Debloating: Built-in protection list prevents accidental uninstallation of critical system apps (e.g., Settings, SystemUI, Google Play Services).

App Recovery: Easily scan for and reinstall any previously removed system app with a single command.

Interactive Filtering: Search/filter apps by name or package keywords (e.g., google, xiaomi, samsung, facebook).

Multi-Package Selection: Select multiple apps at once using simple comma-separated numbers.

Standalone Executable: Can be compiled into a single Portable .exe with zero Python dependencies required for end-users.

📋 Requirements
Android Device: USB Debugging enabled under Developer Options.

PC Connection: USB Cable connecting your device to your computer.

ADB Binary: ADB added to system PATH or placed alongside the executable.

🚀 How to Use
Option 1: Running as a Python Script
Download python for compile
https://www.python.org/downloads/

cmd -
python --version
Python 3.14.6

Clone the repository:

Bash
git clone https://github.com/nano-micro-node/system_app_uninstall_and_recovery.git
cd your-repo-name
Connect your phone via USB and authorize the USB Debugging prompt on your device.

Run the script:

Bash
python app_manager.py
Option 2: Building a Standalone Executable (.exe)
You can compile this tool into a portable single-file executable using PyInstaller.

Install PyInstaller:

Bash
pip install pyinstaller
Build standalone EXE (with ADB bundled):
Place adb.exe, AdbWinApi.dll, and AdbWinUsbApi.dll in the project directory, then run:

DOS
python -m PyInstaller --onefile --console --add-data "adb.exe;." --add-data "AdbWinApi.dll;." --add-data "AdbWinUsbApi.dll;." system_app_uninstall_and_recovery.py

Find your standalone executable in the generated dist/ directory.

🛡️ Protected System Packages
To prevent soft-bricking your device, the tool automatically restricts the uninstallation of core packages, including:

com.android.systemui

com.android.settings

com.google.android.gms

com.android.phone

com.android.providers.settings

com.android.providers.telephony

com.google.android.packageinstaller

⚠️ Disclaimer
Removing critical OEM framework packages can cause certain features to stop working or trigger system crash loops. Always research a package before uninstalling it. If an issue occurs, use Option 2 (Recover) inside the tool to instantly restore the package.

