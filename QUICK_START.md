# Quick Start with UV 🚀

Get ImageSlime running in **under 5 minutes** using uv!

## 🎯 One-Line Setup

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh && cd imageslime && uv sync && uv run python main.py
```

That's it! Open `http://localhost:8000` in your browser.

---

## 📋 Step-by-Step Guide

### 1️⃣ Install UV (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

### 2️⃣ Navigate to Project Directory

```bash
cd imageslime
```

### 3️⃣ Sync Dependencies

```bash
uv sync
```

This will:
- Create a `.venv` directory with all dependencies
- Install ImageSlime in development mode
- Resolve all dependencies from `pyproject.toml`

### 4️⃣ Download SAM3 Model

**Important**: You need the SAM3 model weights (`sam3.pt`) for segmentation to work.

1. Request access at: [https://huggingface.co/facebook/sam3](https://huggingface.co/facebook/sam3)
2. Once approved, download `sam3.pt`
3. Place it in your project directory:
   ```bash
   # Place sam3.pt in the imageslime directory
   mv ~/Downloads/sam3.pt .
   ```

### 5️⃣ Run ImageSlime

```bash
uv run python main.py
```

### 6️⃣ Open Your Browser

Navigate to: `http://localhost:8000`

---

## 🎨 What You Can Do Now

### ✅ Upload Images
- Click the "Upload" button or drag-and-drop images
- Multiple image formats supported (JPEG, PNG, WebP)

### ✅ Segment Objects
- Select the "Segment" tool (or press `2`)
- Click on objects in your images
- SAM3 will automatically create masks

### ✅ Manipulate Objects
- **Move**: Select "Move" tool (press `3`) and drag objects
- **Rotate**: Select "Rotate" tool (press `4`) and rotate objects
- **Scale**: Select "Scale" tool (press `5`) and resize objects
- **Layer Order**: Right-click objects to bring to front/back

### ✅ Manage Layers
- Show/hide layers in the sidebar
- Reorder layers by dragging
- Delete layers you don't need

### ✅ Save & Export
- Save your project for later
- Export compositions as PNG images

---

## 🔧 Common Commands

| Command | Description |
|---------|-------------|
| `uv sync` | Install/update dependencies |
| `uv run python main.py` | Run the server |
| `uv run uvicorn imageslime.main:app --reload` | Run with auto-reload |
| `uv run python test_basic.py` | Run tests |
| `make dev` | Run with auto-reload (using Makefile) |
| `make test` | Run basic tests |
| `make lint` | Run linter |
| `make format` | Format code |

---

## 💡 Tips

### Faster Development

```bash
# Run with auto-reload (code changes take effect immediately)
uv run uvicorn imageslime.main:app --reload
```

### Check SAM3 Status

```bash
# Check if SAM3 model is loaded
uv run python -c "from imageslime.services.segmentation import get_segmentation_service; print(get_segmentation_service().get_model_info())"
```

### Clean Up

```bash
# Remove virtual environment and cache
make clean
```

---

## 🐛 Troubleshooting

### "SAM3 model not available"

Make sure you have:
1. Downloaded `sam3.pt` from Hugging Face
2. Placed it in the project directory
3. The file is named exactly `sam3.pt`

### "uv: command not found"

Install uv first:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Python version not found"

Install Python 3.10+:
```bash
# macOS (with Homebrew)
brew install python@3.10

# Linux (with pyenv)
pyenv install 3.10.13
pyenv global 3.10.13
```

### "Module not found" errors

Always use `uv run` to execute commands:
```bash
# Wrong
python main.py

# Right
uv run python main.py
```

---

## 📚 Learn More

- **Full Documentation**: See `README.md`
- **UV Guide**: See `UV_GUIDE.md`
- **API Documentation**: `http://localhost:8000/api/docs`
- **Project Summary**: See `PROJECT_SUMMARY.md`

---

## 🎉 You're Ready!

Start exploring ImageSlime:

1. ✅ **Install uv**
2. ✅ **Sync dependencies** (`uv sync`)
3. ✅ **Download SAM3 model**
4. ✅ **Run server** (`uv run python main.py`)
5. ✅ **Open browser** (`http://localhost:8000`)

**Happy image editing!** 🎨✨

---

*ImageSlime - Making image editing fun, accessible, and powerful with SAM3 and uv!*