import asyncio
import os
import shutil
import subprocess
import sys
from main import main  # This is your actual bot loop

def ensure_global_install():
    target_dir = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "SensAI")
    exe_path = sys.executable  # This is the current .exe when bundled with PyInstaller

    # Only install if not already installed
    if not os.path.exists(os.path.join(target_dir, "sensai.exe")):
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy2(exe_path, os.path.join(target_dir, "sensai.exe"))

        # Add to PATH if not already there
        current_path = os.environ["PATH"]
        if target_dir not in current_path:
            subprocess.run(f'setx PATH "%PATH%;{target_dir}"', shell=True)
            print(f"\n✅ SensAI installed globally! You can now type `sensai` in any terminal.")
            print("🔁 Restart your CMD or log out/log in to apply PATH changes.\n")
        else:
            print("✔️ Already in PATH. You can now use `sensai` globally.\n")

# Ensure the installation of SensAI globally
ensure_global_install()

# Run the bot loop
if __name__ == "__main__":
    asyncio.run(main())  # Make sure that 'main' in app.py is asynchronous
