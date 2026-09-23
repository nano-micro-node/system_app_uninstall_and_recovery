import os
import shutil
import subprocess
import sys
import time
import traceback

PROTECTED_PACKAGES = {
    "com.android.systemui",
    "com.android.settings",
    "com.google.android.gms",
    "com.android.phone",
    "com.android.providers.settings",
    "com.android.providers.telephony",
    "com.google.android.packageinstaller",
    "com.android.providers.media",
    "com.android.providers.contacts",
}


def get_adb_path() -> str:
    """Locate adb.exe from PyInstaller bundle, local folder, or system PATH."""
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    bundled_adb = os.path.join(base_path, "adb.exe")
    if os.path.exists(bundled_adb):
        return bundled_adb

    return shutil.which("adb") or "adb"


ADB_PATH = get_adb_path()


def run_command(command: list[str]) -> tuple[str, str, int]:
    """Execute shell commands with forced UTF-8 decoding to prevent encoding crashes."""
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as err:
        return "", str(err), 1


def check_adb() -> None:
    """Verify ADB presence and check for connected device."""
    if not os.path.exists(ADB_PATH) and not shutil.which(ADB_PATH):
        print("[ERROR] ADB binary not found in system PATH or program folder.")
        input("Press Enter to exit...")
        sys.exit(1)

    stdout, stderr, code = run_command([ADB_PATH, "devices"])
    lines = [
        line.strip()
        for line in stdout.splitlines()
        if line.strip() and not line.startswith("List of devices")
    ]

    if not lines:
        print("[ERROR] No device connected or authorized.")
        print("Please connect your phone, enable USB Debugging, and authorize the connection.")
        input("Press Enter to exit...")
        sys.exit(1)


def get_system_packages(include_uninstalled: bool = False) -> set[str]:
    """Retrieve system package list using ADB."""
    cmd = [ADB_PATH, "shell", "pm", "list", "packages", "-s"]
    if include_uninstalled:
        cmd.append("-u")

    stdout, _, _ = run_command(cmd)
    packages = set()
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            packages.add(line.replace("package:", "").strip())
    return packages


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def uninstall_mode() -> None:
    clear_screen()
    print("Fetching system packages...\n")
    all_sys_pkgs = get_system_packages(include_uninstalled=False)

    available_pkgs = sorted(list(all_sys_pkgs - PROTECTED_PACKAGES))

    keyword = (
        input(
            "Enter keyword to filter (e.g., google, camera) or press [ENTER] to show ALL: "
        )
        .strip()
        .lower()
    )

    filtered_pkgs = [
        pkg for pkg in available_pkgs if keyword in pkg.lower()
    ]

    if not filtered_pkgs:
        print(f"\n[!] No matching packages found for '{keyword}'.")
        input("\nPress Enter to return to main menu...")
        return

    print(f"\nTotal matching system packages: {len(filtered_pkgs)}")
    print("(Protected system apps are hidden)\n")

    print("+------+--------------------------------------------------+")
    print("| #    | Package Name                                     |")
    print("+------+--------------------------------------------------+")
    for idx, pkg in enumerate(filtered_pkgs, 1):
        print(f"| {idx:<4} | {pkg:<48} |")
    print("+------+--------------------------------------------------+")

    choice = input(
        "\nEnter serial numbers to uninstall (comma separated, e.g. 1,3,5): "
    ).strip()

    if not choice:
        print("No selection made.")
        time.sleep(1)
        return

    selected_indices = []
    for item in choice.split(","):
        item = item.strip()
        if item.isdigit() and int(item) > 0:
            selected_indices.append(int(item))

    print("\nStarting uninstall...\n")
    for idx in selected_indices:
        if 1 <= idx <= len(filtered_pkgs):
            pkg = filtered_pkgs[idx - 1]
            if pkg in PROTECTED_PACKAGES:
                print(f"[BLOCKED] {pkg} is a protected system app. Skipped.")
            else:
                print(f"Uninstalling [{idx}]: {pkg}")
                stdout, stderr, _ = run_command(
                    [
                        ADB_PATH,
                        "shell",
                        "pm",
                        "uninstall",
                        "-k",
                        "--user",
                        "0",
                        pkg,
                    ]
                )
                output = (stdout + stderr).strip()
                print(f" -> {output if output else 'Done'}")
        else:
            print(f"[WARN] Serial number {idx} not found.")

    print("\n============================================")
    print("Uninstall Complete.")
    print("============================================")
    input("Press Enter to return to menu...")


def recover_mode() -> None:
    clear_screen()
    print("Scanning for uninstalled (hidden) system apps...\n")

    all_sys_pkgs = get_system_packages(include_uninstalled=True)
    inst_sys_pkgs = get_system_packages(include_uninstalled=False)

    uninstalled_pkgs = sorted(list(all_sys_pkgs - inst_sys_pkgs))

    keyword = (
        input(
            "Enter keyword to filter (e.g., xiaomi, chrome) or press [ENTER] to show ALL: "
        )
        .strip()
        .lower()
    )

    filtered_pkgs = [
        pkg for pkg in uninstalled_pkgs if keyword in pkg.lower()
    ]

    if not filtered_pkgs:
        print("\nNo matching uninstalled system apps found.")
        input("\nPress Enter to return to main menu...")
        return

    print(
        f"\nFound {len(filtered_pkgs)} matching uninstalled system app(s):\n"
    )
    print("+------+--------------------------------------------------+")
    print("| #    | Package Name                                     |")
    print("+------+--------------------------------------------------+")
    for idx, pkg in enumerate(filtered_pkgs, 1):
        print(f"| {idx:<4} | {pkg:<48} |")
    print("+------+--------------------------------------------------+")

    print("\nOptions:")
    print("- Enter specific serial numbers (e.g. 1,3,5)")
    print('- Type "all" to restore ALL listed items')

    choice = input("\nYour choice: ").strip().lower()

    if choice == "all":
        print("\nRestoring ALL listed apps...\n")
        for idx, pkg in enumerate(filtered_pkgs, 1):
            print(f"Restoring [{idx}]: {pkg}")
            run_command(
                [ADB_PATH, "shell", "cmd", "package", "install-existing", pkg]
            )
    elif choice:
        selected_indices = []
        for item in choice.split(","):
            item = item.strip()
            if item.isdigit() and int(item) > 0:
                selected_indices.append(int(item))

        print("\nRestoring selected apps...\n")
        for idx in selected_indices:
            if 1 <= idx <= len(filtered_pkgs):
                pkg = filtered_pkgs[idx - 1]
                print(f"Restoring [{idx}]: {pkg}")
                run_command(
                    [
                        ADB_PATH,
                        "shell",
                        "cmd",
                        "package",
                        "install-existing",
                        pkg,
                    ]
                )
            else:
                print(f"[WARN] Serial {idx} not found.")
    else:
        print("No selection made.")
        time.sleep(1)
        return

    print("\n============================================")
    print("Recovery Complete.")
    print("============================================")
    input("Press Enter to return to menu...")


def menu_loop() -> None:
    check_adb()

    while True:
        clear_screen()
        print("============================================")
        print("Android System App Manager (ADB Python)")
        print("============================================")
        print()
        print("1. Uninstall System App")
        print("2. Recover (Restore) System App")
        print("3. Exit")
        print()

        choice = input("Select option: ").strip()

        if choice == "1":
            uninstall_mode()
        elif choice == "2":
            recover_mode()
        elif choice == "3":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice.")
            time.sleep(1)


def main() -> None:
    try:
        menu_loop()
    except Exception:
        print("\n[CRITICAL ERROR] The application encountered an error:")
        traceback.print_exc()
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()