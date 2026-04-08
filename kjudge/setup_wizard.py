"""
setup_wizard.py — Interactive installer and uninstaller for standalone kjudge.

Handles automatically moving kjudge.exe to a permanent location
and injecting it into the Windows PATH, or fully cleansing it.
"""

import os
import sys
import shutil
import subprocess
import time

from kjudge.utils import console, print_success, print_error, print_warning

def is_frozen():
    """Check if we are running as a PyInstaller executable."""
    return getattr(sys, 'frozen', False)

def get_install_dir():
    """Get the target installation directory for the executable."""
    home = os.path.expanduser("~")
    return os.path.join(home, ".kjudge", "bin")

def add_to_path(target_dir: str):
    """Safely append target_dir to the User Windows PATH via PowerShell."""
    if os.name != 'nt':
        return False
        
    ps_command = f"""
    $targetPath = "{target_dir}"
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notmatch [regex]::Escape($targetPath)) {{
        $newPath = $userPath + ";" + $targetPath
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Output "ADDED"
    }} else {{
        Write-Output "EXISTS"
    }}
    """
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_command],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        return "ADDED" in res.stdout
    except Exception:
        return False

def remove_from_path(target_dir: str):
    """Remove target_dir from the User Windows PATH."""
    if os.name != 'nt':
        return
        
    ps_command = f"""
    $targetPath = "{target_dir}"
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -match [regex]::Escape($targetPath)) {{
        # Split by semicolon, filter out the target, rejoin
        $paths = $userPath -split ';' | Where-Object {{ $_ -ne "" -and $_ -ne $targetPath }}
        $newPath = $paths -join ';'
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    }}
    """
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_command], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception:
        pass

def run_interactive_setup():
    """Run an interactive installer if double-clicked with no args."""
    console.print("\n[bold cyan]⚡ Welcome to the kjudge CLI Setup ⚡[/]\n")
    
    install_dir = get_install_dir()
    exe_name = os.path.basename(sys.executable)
    target_exe = os.path.join(install_dir, exe_name)
    
    if os.path.exists(target_exe) and sys.executable.lower() == target_exe.lower():
        # Already running from the installed location
        console.print("[green]kjudge is already installed correctly on your system![/]")
        console.print("You can open any Terminal/Command Prompt and type [bold]kjudge[/]\n")
        input("Press Enter to exit...")
        return

    console.print("It looks like you opened the standalone executable directly.")
    console.print("Would you like to permanently install kjudge to your system?")
    console.print(f"This will copy it to [dim]{install_dir}[/] and add it to your PATH.\n")
    
    choice = input("Install kjudge? (Y/n): ").strip().lower()
    
    if choice in ['', 'y', 'yes']:
        try:
            os.makedirs(install_dir, exist_ok=True)
            # Copy self to install dir
            shutil.copy2(sys.executable, target_exe)
            
            # Add to PATH
            added = add_to_path(install_dir)
            
            console.print("\n[bold green]✓ Installation Complete![/]")
            if added:
                console.print("Successfully added to your System PATH.")
            else:
                console.print("Path was already configured.")
                
            console.print("\n[bold]You must completely restart your terminal for changes to take effect.[/]")
            console.print("After restarting, simply type [cyan]kjudge[/] in any folder.\n")
            
        except Exception as e:
            print_error(f"Failed to install: {e}")
    else:
        console.print("\n[dim]Installation cancelled.[/]")
        
    input("Press Enter to exit...")

def handle_self_install(args):
    """CLI handler for 'kjudge self-install'"""
    if not is_frozen():
        print_error("self-install is only available for the standalone compiled executable.")
        sys.exit(1)
        
    install_dir = get_install_dir()
    target_exe = os.path.join(install_dir, os.path.basename(sys.executable))
    
    os.makedirs(install_dir, exist_ok=True)
    shutil.copy2(sys.executable, target_exe)
    add_to_path(install_dir)
    print_success(f"kjudge installed to {target_exe} and added to PATH.")

def handle_self_uninstall(args):
    """CLI handler for 'kjudge self-uninstall'"""
    console.print("[bold red]⚠ WARNING: Deep Uninstall[/]")
    console.print("This will completely remove:")
    console.print("1. The kjudge executable from your PATH.")
    console.print("2. Your entire ~/.kjudge directory (including all global configs and templates!).")
    console.print("Note: Local project folders (.kjudge/ inside your code folders) will NOT be deleted.\n")
    
    verify = input("Type 'UNINSTALL' to confirm: ").strip()
    if verify != "UNINSTALL":
        console.print("[dim]Aborted.[/]")
        return
        
    install_dir = get_install_dir()
    kjudge_root = os.path.expanduser("~/.kjudge")
    
    console.print("\n[dim]Removing from PATH...[/]")
    remove_from_path(install_dir)
    
    console.print(f"[dim]Deleting {kjudge_root}...[/]")
    
    # We cannot delete the executable if we are currently running it!
    # So if we are running from inside kjudge_root, we need to schedule a self-delete or warn.
    running_from_inside = is_frozen() and sys.executable.startswith(kjudge_root)
    
    if running_from_inside:
        # Schedule delete on reboot or use cmd /c trick
        # A simple trick to delete self after exit on windows:
        if os.name == 'nt':
            cmd = f'ping 127.0.0.1 -n 2 > nul & rmdir /s /q "{kjudge_root}"'
            subprocess.Popen(["cmd.exe", "/c", cmd], creationflags=subprocess.CREATE_NO_WINDOW)
            print_success("Uninstall initiated. kjudge will completely self-destruct when this window closes.")
            sys.exit(0)
    else:
        try:
            if os.path.exists(kjudge_root):
                shutil.rmtree(kjudge_root, ignore_errors=True)
            print_success("kjudge has been completely uninstalled from your system.")
        except Exception as e:
            print_error(f"Error during uninstall: {e}")
