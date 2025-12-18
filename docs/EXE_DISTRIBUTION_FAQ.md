# EXE Distribution Q&A

## ✅ EXE Runs 100% INDEPENDENTLY

**No Python Installation Required!**

The exe is a **complete standalone application** containing:

- Python 3.11 runtime
- PySide6 (Qt framework)
- All your code (core/, ui/, simulator.py)
- All dependencies

### Distribution Test:

1. Copy `dist\CircuitPlaygroundPro.exe` to any Windows PC
2. Double-click to run
3. Works immediately - no installation!

### What Users Need:

- **Operating System:** Windows 10/11 (64-bit) ⚠️ _Windows only - EXE is Windows-specific_
- **No Python:** Doesn't matter if Python is installed or not
- **No PySide6:** Already included in the exe
- **No pip packages:** Everything is bundled

### For Linux/Mac Users:

The EXE is **Windows-only**. Linux/Mac users should run the Python source:

```bash
pip install PySide6
python app.py
```

---

## 📁 Extra Files Explained

When you run `python build.py`, PyInstaller creates several files/folders:

### 1. **build/** Folder (TEMPORARY)

**Purpose:** PyInstaller's working directory  
**Contents:** Intermediate build files, dependency analysis  
**Keep it?** ❌ NO - Can be deleted after build

**What's inside:**

- Analysis of your Python dependencies
- Compiled Python bytecode
- Temporary C files
- Build logs

### 2. **CircuitPlaygroundPro.spec** File

**Purpose:** PyInstaller configuration file  
**Contents:** Build instructions (auto-generated from build.py)  
**Keep it?** ⚠️ OPTIONAL - Useful for rebuilding

**What it does:**

- Tells PyInstaller what to include/exclude
- Configures exe name, icon, hidden imports
- Can be edited for custom builds

**You can rebuild using the spec:**

```powershell
pyinstaller CircuitPlaygroundPro.spec
```

### 3. **dist/** Folder (KEEP THIS!)

**Purpose:** Final output directory  
**Contents:** Your distributable exe  
**Keep it?** ✅ YES - This is what you distribute!

This is your **ready-to-ship** application.

### 4. **pycache** Folders

**Purpose:** Python bytecode cache (for development)  
**Keep it?** ❌ NO - Not needed for exe distribution

---

## 📦 What to Distribute

**Only distribute:**

```
dist/CircuitPlaygroundPro.exe
```

**That's it!** One file.

## 🚀 Distribution Checklist

### For End Users (Simple):

1. ✅ Copy `dist\CircuitPlaygroundPro.exe`
2. ✅ Send to user
3. ✅ User double-clicks to run
4. ✅ App creates `save_files/` folder automatically on first save

## 💡 Pro Tips

### 1. Create ZIP for Distribution

```powershell
Compress-Archive -Path "dist\CircuitPlaygroundPro.exe" -DestinationPath "CircuitPlaygroundPro_v2.0.zip"
```

### 2. Include README

```
CircuitPlaygroundPro_v2.0.zip:
├── CircuitPlaygroundPro.exe
└── README.txt  (from DISTRIBUTION_README.txt)
```

### 3. Antivirus Note

Some antivirus software flags PyInstaller exes as suspicious.  
This is a **false positive** - the exe is safe.  
If flagged, user should add an exception.

---

## ❓ FAQ

**Q: Can I rename the exe?**  
A: Yes! Rename to anything: `MyCircuitApp.exe`, `LogicSim.exe`, etc.

**Q: Can users uninstall it?**  
A: Yes - just delete the exe. No registry entries, no installation.

**Q: Will it work on Windows 7?**  
A: Probably not - PySide6 requires Windows 10+

**Q: Can I run multiple instances?**  
A: Yes! Open it multiple times if needed.

**Q: Where do error logs go?**  
A: None - it's windowed mode. For debugging, rebuild without `--windowed`

---
