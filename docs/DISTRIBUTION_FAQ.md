# Executable Distribution Q&A

## ✅ Portable & Independent

The application is a **complete standalone package**. No Python installation or separate libraries are required on the target PC—everything it needs is bundled inside.

---

## 📦 What to Distribute?

Depending on which build tool you used, your "Ready-to-Ship" output will be in a different location:

### 1. Single-File Distribution (The Easiest)
Best for casual sharing. Just send the one file!

| Build Tool | Output File | Location |
| :--- | :--- | :--- |
| **PyInstaller** | `CircuitPlaygroundPro` | `dist/` folder |
| **Nuitka** | `CircuitPlaygroundPro` | Project Root |

### 2. Folder-Based Distribution (The Fastest)
Best for professional distribution or older PCs. **You must send the entire folder!**

| Build Tool | Output Folder | Location |
| :--- | :--- | :--- |
| **PyInstaller** | `CircuitPlaygroundPro/` | `dist/` folder |
| **Nuitka** | `app.dist/` | Project Root |

> [!IMPORTANT]
> **Don't just send the executable from a folder build!** If you move the executable out of its folder alone, it will crash because it can't find its "internal" organs (DLLs). Always ZIP the whole folder before sending.

---

## 📁 Temporary Folders & Files 

### **build/**
Created by PyInstaller to prepare the build. 
*   **Keep it?** ❌ NO - You can safely delete this after the build is successful to save space.

### **CircuitPlaygroundPro.spec**
This sometimes gets created when you run `build.py`.
*   **Keep it?** ❌ NO - You can safely delete this after the build is complete.

---

## 🚀 Distribution Checklist

- **One-File Delivery**: If using `--onefile`, you only need to send the single executable.
- **Folder Delivery**: If using `--onedir`, you **MUST** send the entire folder. I recommend zipping it first (Right-click > Compress/Zip).
- **User Permissions**: Saved circuits and settings are stored in the user's **Documents** folder:
    - **Windows**: `C:\Users\<User>\Documents\CircuitPlaygroundPro`
    - **macOS**: `/Users/<User>/Documents/CircuitPlaygroundPro`
    - **Linux**: `/home/<User>/Documents/CircuitPlaygroundPro` (or your local Documents path)
    
    This ensures your files are safe and accessible even if you move the executable, and prevents OS security from blocking folder creation. 
    
    *Note: If the application cannot access your Documents folder (e.g., due to strict security settings), it will automatically fall back to a local `save_files` folder in the application's root directory.*

## 💡 Pro Tips

### 1. The ZIP "Wrapper"
Always ZIP your distribution (whether it's one file or a folder). It protects the binary from being corrupted during download and sometimes prevents aggressive Antivirus software from blocking it immediately.

### 2. Antivirus False Positives
Some antivirus software flags newly created executables as "Unknown". This is common for PyInstaller/Nuitka apps. The app is 100% clean, but first-time users may need to click "Run anyway" or add an exclusion.

---

## ❓ FAQ

**Q: Can I rename the executable?**
A: Yes! You can rename the executable to anything. In a **folder build**, just make sure the name change doesn't break the relative paths (usually, it's fine).

**Q: Where is the Python Interpreter?**
A: It's converted/bundled inside. The user never needs to know Python even exists!

**Q: Can I make standalone versions for Linux or Mac?**
A: **Yes!** If you run the build scripts on those systems, you get native versions:

*   **Linux**: `CircuitPlaygroundPro` (No extension)
    - **What is an AppImage?** It's a single file that works like a "Portable App". It contains everything the app needs and runs on almost any Linux version. You just right-click it, select "Allow executing file as program", and double-click.
*   **macOS**: `CircuitPlaygroundPro.app` (App Bundle)
    - **Created By**: `build.py` or `nuitka_build.py`. This is the **actual program**.
    - **What is a `.app`?** It's a special folder that macOS displays as a single double-clickable icon.
    - **What about `.dmg`?** The build scripts **do not** create a `.dmg`. A `.dmg` (Disk Image) is a "shipping container" that you create manually *after* the build to share the app professionally using a separate command-line tool (like `create-dmg` or macOS's built-in `Disk Utility`). Users open the `.dmg` to drag the `.app` into their Applications folder.

*Note: Because we are building "Native" code, you must run the build on the target operating system (e.g., use a Mac to build for Mac).*

**Q: How do I "Uninstall"?**
A: Just delete the file or folder. No registry changes are made by this app.

**📖 Back to [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)**

---