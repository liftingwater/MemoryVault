# 🚀 How to Start MemoryVault Locally

## Easiest Way (Automated Setup)

### Option A: Run Setup Script (Recommended)

```bash
# Run the setup script (does everything for you)
./setup.sh
```

This will:
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Show you next steps

Then:
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Run the app
python app.py

# 3. Open browser to http://localhost:5000
```

---

## Manual Setup (If You Prefer)

### Step 1: Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate  # On Windows
```

You should see `(venv)` in your terminal prompt.

---

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask 3.0.0
- python-dotenv 1.0.0

---

### Step 3: Run the Application

```bash
python app.py
```

You should see output like:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

---

### Step 4: Open in Browser

Open your web browser and go to:
```
http://localhost:5000
```

You should see the **MemoryVault Card Creation UI**! 🎉

---

## What You Can Do Now

### ✅ Create Cards

1. **Choose content type** for front (Text or Image)
2. **Enter content** (text or image URL)
3. **Choose content type** for back (Text or Image)
4. **Enter content** (text or image URL)
5. **Click "Create Card"**

### 📝 Try These Examples

**Text Card:**
- Front: "What is the capital of France?"
- Back: "Paris"

**Image Card:**
- Front (Image): `https://picsum.photos/400/300`
- Back (Text): "A random beautiful image"

**Mixed Card:**
- Front (Text): "What landmark is this?"
- Back (Image): `https://source.unsplash.com/random/400x300`

---

## Features Currently Working

✅ Card creation UI  
✅ Text and image content support  
✅ Live preview with flip animation  
✅ Form validation  
✅ Responsive design  

⚠️ **Note:** Cards are NOT saved yet (backend integration coming next)

---

## Troubleshooting

### Problem: `python3: command not found`
**Solution:** Try `python` instead of `python3`
```bash
python -m venv venv
python app.py
```

### Problem: `ModuleNotFoundError: No module named 'flask'`
**Solution:** Make sure you activated the virtual environment and installed dependencies
```bash
source venv/bin/activate  # Activate venv
pip install -r requirements.txt  # Install dependencies
```

### Problem: Port 5000 already in use
**Solution:** Kill the process using port 5000 or use a different port
```bash
# Find and kill process on port 5000 (Mac/Linux)
lsof -ti:5000 | xargs kill -9

# Or run on a different port
flask run --port 5001
```

### Problem: `TemplateNotFound: index.html`
**Solution:** Make sure you're in the project root directory
```bash
pwd  # Should show: /Users/ealexanderwheeldon/Development/MemoryVault
ls templates/  # Should show: index.html
```

---

## Stopping the Application

Press `Ctrl + C` in the terminal where the app is running.

---

## Deactivating Virtual Environment

When you're done:
```bash
deactivate
```

---

## Next Time You Want to Run It

```bash
# 1. Navigate to project directory
cd /Users/ealexanderwheeldon/Development/MemoryVault

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run the app
python app.py

# 4. Open browser to http://localhost:5000
```

---

## Project Structure

```
MemoryVault/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── models/             # Data models
│   ├── card.py
│   └── content.py
├── templates/          # HTML templates
│   └── index.html
├── static/             # CSS, JavaScript, images
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── docs/               # Documentation
```

---

## What's Next?

After you've tried the UI, you can:

1. **Implement the database** (see `docs/IMPLEMENTATION_PLAN.md`)
2. **Add file upload** for images and audio
3. **Build the review interface** for studying cards
4. **Add user authentication**

See `docs/README.md` for the full implementation roadmap.

---

## Need Help?

- Check `QUICKSTART.md` for more details
- Review `docs/README.md` for architecture documentation
- Look at `API_EXAMPLES.md` for API usage examples

---

**Enjoy building your Leitner box app! 🎓📚**

