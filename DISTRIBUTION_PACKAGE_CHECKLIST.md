# NukeWorks Distribution Package - Checklist

## ✅ What to Send to Your Friend

### Required Files/Folders

- [ ] **`dist\NukeWorks\`** folder (contains):
  - [ ] `NukeWorks.exe` - Main executable
  - [ ] `_internal\` - All dependencies (entire folder)
- [ ] **`README_FOR_DISTRIBUTION.md`** - User setup guide

- [ ] **`TROUBLESHOOTING_GUIDE_FOR_USERS.md`** - Problem-solving guide

- [ ] **`create_database.py`** - Database initialization script

### Optional but Recommended

- [ ] **Sample database file** - Pre-initialized `sample_database.sqlite` with default admin user
  - To create: Run `python create_database.py sample_database.sqlite` in your environment
  - Makes setup easier - they can just select this file

### Do NOT Send

- ❌ `venv\` folder (virtual environment)
- ❌ `build\` folder (build artifacts)
- ❌ `__pycache__\` folders
- ❌ `.env` file (your local config)
- ❌ Your personal database files (unless intentional)
- ❌ Development scripts not needed by end users

## 📦 How to Package

### Option 1: Zip File (Recommended)

```
NukeWorks_Distribution.zip
├── NukeWorks\
│   ├── NukeWorks.exe
│   └── _internal\
│       └── [all dependency files]
├── README_FOR_DISTRIBUTION.md
├── TROUBLESHOOTING_GUIDE_FOR_USERS.md
├── create_database.py
└── sample_database.sqlite (optional)
```

Create zip:

1. Create folder: `NukeWorks_Distribution`
2. Copy `dist\NukeWorks\` folder into it
3. Copy the 3 markdown/python files into it
4. Optionally add `sample_database.sqlite`
5. Zip the entire `NukeWorks_Distribution` folder
6. Send the zip file

### Option 2: OneDrive/Dropbox Share

Upload the same folder structure, share link

## 📧 Message Template for Your Friend

```
Hi [Friend],

I'm sending you NukeWorks - here's how to get started:

1. UNZIP the entire package to a folder (e.g., Desktop\NukeWorks)
   ⚠️ IMPORTANT: Unzip everything, don't run from inside the zip!

2. RUN NukeWorks.exe (double-click it)
   - A terminal window will open (keep it visible)
   - Your browser will open automatically

3. FIRST TIME SETUP:
   Option A (Easier):
   - Select "sample_database.sqlite" from the list
   - Login: admin / admin123

   Option B (Create your own):
   - Follow steps in README_FOR_DISTRIBUTION.md
   - Run: python create_database.py my_database.sqlite
   - Then select the file you created

4. CHANGE PASSWORD immediately after first login!

If you have any issues:
- Keep the terminal window open and visible
- Check TROUBLESHOOTING_GUIDE_FOR_USERS.md
- Copy the terminal output and send it to me

Let me know if you need help!
```

## 🧪 Pre-Distribution Testing

### Test on YOUR machine first:

- [ ] Delete `instance\db_selector.json` (simulate fresh install)
- [ ] Run `dist\NukeWorks\NukeWorks.exe`
- [ ] Verify browser opens to database selection (not login)
- [ ] Create a test database using `create_database.py`
- [ ] Select the database and verify login works
- [ ] Check terminal shows helpful debug output
- [ ] Read through both documentation files
- [ ] Verify all instructions are clear

### Test with empty/wrong database (optional):

- [ ] Try logging in with empty .sqlite file → Should show "no users" error
- [ ] Try with wrong username → Should list available usernames
- [ ] Try with missing database → Should show file not found error

## 🔍 Expected First-Run Experience (Your Friend's View)

1. **Extract & Run**

   - Unzip folder
   - Double-click `NukeWorks.exe`
   - Terminal opens with startup info

2. **Terminal Shows:**

   ```
   ============================================================
   NukeWorks - Nuclear Project Management Database
   ============================================================
   Environment: development
   Python Version: 3.13.2
   Working Directory: C:\Users\Friend\Desktop\NukeWorks
   ...
   📋 FIRST TIME SETUP:
      1. Browser will open to database selection page
      2. Select or browse to a .sqlite database file
      3. If database is empty, you'll need to initialize it
      4. Default login: admin / admin123
   ```

3. **Browser Opens:**

   - Shows "Select Database" page
   - Lists any .sqlite files found
   - Shows "Browse" button

4. **After Selecting Database:**

   - Shows "Login" page
   - Enter: admin / admin123
   - Redirects to dashboard

5. **If Problems:**
   - Terminal shows `[DEBUG]` and `[CRITICAL]` messages
   - User checks TROUBLESHOOTING_GUIDE_FOR_USERS.md
   - Or sends you terminal output

## 🆘 Common Issues & Quick Fixes

### Issue: "Can't find database"

**Fix:** Include `sample_database.sqlite` in package

### Issue: "Login fails - user not found"

**Fix:** Database needs initialization

- Send pre-initialized database, OR
- User runs: `python create_database.py their_database.sqlite`

### Issue: "Python not found"

**Fix:** For database creation only

- Send pre-initialized database so Python not needed, OR
- User installs Python from python.org

### Issue: "NukeWorks.exe won't run"

**Fix:**

- Windows security blocked it → Right-click → Properties → Unblock
- Antivirus blocked it → Add exception
- Missing files → Re-extract entire zip

## 📊 Size Estimates

- Executable package: ~100-150 MB
- Sample database: ~200 KB
- Documentation: ~50 KB
- **Total zip file: ~100-150 MB**

## 🔒 Security Reminders

- [ ] Remind friend to change admin password immediately
- [ ] Don't include any real/sensitive data in sample database
- [ ] If sharing real database, ensure it's encrypted/secure channel

## ✨ Optional Enhancements

### For Better UX:

1. **Desktop Shortcut**

   - Create shortcut to `NukeWorks.exe`
   - Name it "NukeWorks"
   - Include in package

2. **Quick Start Guide** (one-page PDF)

   - Visual screenshots
   - Step-by-step with images
   - Print-friendly

3. **Pre-Configured Database**
   - Include database with some sample data
   - Shows what the system can do
   - User can experiment safely

## 📞 Support Plan

**Be ready to help with:**

- [ ] Unzipping issues
- [ ] Database selection confusion
- [ ] Login problems (most common)
- [ ] Terminal output interpretation
- [ ] Database creation if needed

**Ask for:**

- Terminal output (full text)
- What they clicked
- What error messages they see
- Screenshot if helpful

---

## ✅ Final Checklist Before Sending

- [ ] Tested executable on your machine
- [ ] All required files included
- [ ] Documentation is clear and complete
- [ ] Sample database included (recommended)
- [ ] Zip file created or share link ready
- [ ] Message to friend prepared
- [ ] Ready to provide support if needed

---

**Good luck! The enhanced debug output should make troubleshooting much easier.**



