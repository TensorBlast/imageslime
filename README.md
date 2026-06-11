# ImageSlime 🎨

**Interactive Image Segmentation and Editing Tool using SAM3**

ImageSlime is a browser-based image editor that leverages Meta's Segment Anything Model 3 (SAM3) to provide powerful segmentation capabilities. With ImageSlime, you can:

- Upload and manage multiple images
- Click to select and segment objects using SAM3
- Extract segmented objects and manipulate them independently
- Arrange objects in layers with drag-and-drop
- Rotate, scale, and reposition objects
- Save and export your creations

## Features ✨

### 🎯 Segmentation
- **Point-based segmentation**: Click on objects to segment them
- **Bounding box segmentation**: Draw boxes around objects
- **Text-based segmentation**: Use text prompts to find objects (SAM3 concept segmentation)
- **Pre-computed embeddings**: Fast segmentation by caching image embeddings

### 📦 Object Manipulation
- **Drag and drop**: Move objects around the canvas
- **Rotate**: Rotate objects to any angle
- **Scale**: Resize objects proportionally or freely
- **Layer ordering**: Bring objects to front or send to back
- **Delete**: Remove unwanted objects

### 🎨 Layer Management
- **Multiple layers**: Work with multiple images simultaneously
- **Visibility control**: Show/hide layers
- **Layer ordering**: Reorder layers in the composition
- **Opacity control**: Adjust layer transparency

### 💾 Project Management
- **Save projects**: Save your work for later
- **Load projects**: Continue working on saved projects
- **Export**: Download your final composition as an image

## Installation 🚀

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- A CUDA-enabled GPU (recommended for SAM3)
- At least 8GB of RAM (16GB+ recommended for SAM3)

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/imageslime.git
   cd imageslime
   ```

2. **Install dependencies with uv** (recommended):
   ```bash
   # Install uv if you don't have it
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Sync dependencies
   uv sync
   ```

   **OR with pip**:
   ```bash
   pip install -e .
   ```

   **OR create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

4. **Run the server**:
   
   **With uv**:
   ```bash
   uv run python main.py
   ```
   
   **With pip**:
   ```bash
   python main.py
   ```

5. **Download SAM3 model weights**:
   
   SAM3 requires the model weights file (`sam3.pt`). You need to:
   
   a. Request access to the SAM3 model on [Hugging Face](https://huggingface.co/facebook/sam3)
   b. Once approved, download `sam3.pt` from the model page
   c. Place the file in your project directory or specify its path in `.env`

   Alternatively, you can set the model path in the `.env` file:
   ```bash
   echo "SAM3_MODEL_PATH=/path/to/sam3.pt" >> .env
   ```

5. **Start the server**:
   ```bash
   python main.py
   ```

6. **Open your browser**:
   Navigate to `http://localhost:8000` to access ImageSlime

## Usage 📖

### Quick Start

1. **Upload an image**: Click the "Upload" button or drag and drop images onto the canvas
2. **Segment objects**: 
   - Select the "Segment" tool (or press `2`)
   - Click on the object you want to segment
   - The object will be extracted and added to your objects list
3. **Manipulate objects**:
   - Select the "Move" tool (or press `3`) to drag objects
   - Select the "Rotate" tool (or press `4`) to rotate objects
   - Select the "Scale" tool (or press `5`) to resize objects
4. **Layer management**:
   - Use the sidebar to show/hide layers
   - Drag layers to reorder them
   - Delete layers you no longer need
5. **Export**: Click "Export" to download your composition as an image

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` | Select tool |
| `2` | Segment tool |
| `3` | Move tool |
| `4` | Rotate tool |
| `5` | Scale tool |
| `Escape` | Cancel current operation |
| `Delete` / `Backspace` | Delete selected object |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |

### Right-Click Menu

Right-click on objects to access the context menu with options:
- **Bring to Front**: Move object to the top layer
- **Send to Back**: Move object to the bottom layer
- **Delete**: Remove the object
- **Copy**: Duplicate the object

## API Documentation 📡

ImageSlime provides a RESTful API for programmatic access. The API documentation is available at:

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/openapi.json`

### API Endpoints

#### Images
- `POST /api/v1/images/upload` - Upload an image
- `GET /api/v1/images/{image_id}` - Get an image
- `GET /api/v1/images/{image_id}/thumbnail` - Get image thumbnail
- `DELETE /api/v1/images/{image_id}` - Delete an image
- `POST /api/v1/images/{image_id}/compute-embeddings` - Compute embeddings
- `GET /api/v1/images/list` - List all images

#### Segmentation
- `POST /api/v1/segmentation/points` - Segment with points
- `POST /api/v1/segmentation/box` - Segment with bounding box
- `POST /api/v1/segmentation/text` - Segment with text prompt
- `GET /api/v1/segmentation/model-info` - Get model information
- `POST /api/v1/segmentation/clear-cache` - Clear embedding cache

#### Layers
- `POST /api/v1/layers/create` - Create a new layer
- `GET /api/v1/layers/{layer_id}` - Get layer information
- `PUT /api/v1/layers/{layer_id}` - Update layer
- `POST /api/v1/layers/{layer_id}/move-front` - Move layer to front
- `POST /api/v1/layers/{layer_id}/move-back` - Move layer to back
- `POST /api/v1/layers/{layer_id}/move-up` - Move layer up
- `POST /api/v1/layers/{layer_id}/move-down` - Move layer down
- `DELETE /api/v1/layers/{layer_id}` - Delete layer
- `GET /api/v1/layers/list` - List all layers

#### Project
- `POST /api/v1/project/create` - Create a new project
- `POST /api/v1/project/save` - Save current project
- `POST /api/v1/project/load` - Load a project
- `GET /api/v1/project/export/{project_id}` - Export project as image
- `GET /api/v1/project/list` - List saved projects
- `DELETE /api/v1/project/{project_id}` - Delete a project

## Configuration ⚙️

ImageSlime can be configured using environment variables or a `.env` file.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host address |
| `PORT` | `8000` | Server port |
| `DEBUG` | `True` | Enable debug mode |
| `SAM3_MODEL_PATH` | `sam3.pt` | Path to SAM3 model weights |
| `SAM3_DEVICE` | `cuda` | Device to run SAM3 on (`cuda` or `cpu`) |
| `SAM3_HALF_PRECISION` | `True` | Use FP16 for faster inference |
| `UPLOAD_DIR` | `uploads` | Directory for uploaded images |
| `TEMP_DIR` | `temp` | Directory for temporary files |
| `MAX_IMAGE_SIZE` | `4096` | Maximum image dimension in pixels |
| `MAX_UPLOAD_SIZE` | `10485760` | Maximum upload size in bytes (10MB) |
| `EMBEDDING_CACHE_SIZE` | `10` | Number of image embeddings to cache |
| `SEGMENTATION_CONFIDENCE` | `0.25` | Minimum confidence for segmentation |

### Example `.env` File

```bash
# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# SAM3 configuration
SAM3_MODEL_PATH=/path/to/sam3.pt
SAM3_DEVICE=cuda
SAM3_HALF_PRECISION=True

# Storage configuration
UPLOAD_DIR=./uploads
TEMP_DIR=./temp

# Performance settings
EMBEDDING_CACHE_SIZE=20
SEGMENTATION_CONFIDENCE=0.3
```

## Troubleshooting 🐛

### SAM3 Model Not Available

If you see "SAM3 model not available" in the status bar:

1. Ensure you have downloaded `sam3.pt` from Hugging Face
2. Place the file in your project directory or specify its path in `.env`
3. Make sure you have enough GPU memory (SAM3 requires ~4GB VRAM)
4. Check that you have the correct version of ultralytics: `pip install -U ultralytics>=8.3.237`

### CUDA Errors

If you encounter CUDA errors:

1. Ensure you have NVIDIA drivers installed
2. Install CUDA Toolkit (version compatible with your GPU)
3. Install cuDNN
4. Set `SAM3_DEVICE=cpu` in `.env` to use CPU (slower but works without GPU)

### Out of Memory Errors

SAM3 is a large model and requires significant memory:

1. Use a GPU with at least 8GB VRAM
2. Set `SAM3_HALF_PRECISION=True` to use FP16 (reduces memory usage)
3. Reduce `EMBEDDING_CACHE_SIZE` to cache fewer embeddings
4. Use smaller images (reduce `MAX_IMAGE_SIZE`)

### Slow Performance

For better performance:

1. Use a GPU with CUDA support
2. Enable half precision: `SAM3_HALF_PRECISION=True`
3. Pre-compute embeddings for frequently used images
4. Reduce the number of cached embeddings if not needed

## Architecture 🏗️

### Backend

- **Framework**: FastAPI (Python)
- **Segmentation**: Ultralytics SAM3
- **Image Processing**: OpenCV, Pillow
- **Data Models**: Pydantic

### Frontend

- **Canvas**: HTML5 Canvas API
- **UI**: Vanilla JavaScript with modern CSS
- **Communication**: Fetch API for HTTP requests

### Data Flow

```
User Interaction (Browser)
        ↓
    HTTP Request (Fetch API)
        ↓
    FastAPI Endpoint
        ↓
    SAM3 Segmentation Service
        ↓
    Return Segmentation Results
        ↓
    Update Canvas (Browser)
```

## Contributing 🤝

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add your feature'`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Open a Pull Request

## License 📜

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

- [Meta AI](https://ai.meta.com/) for the Segment Anything Model (SAM3)
- [Ultralytics](https://ultralytics.com/) for the SAM3 integration
- All contributors and users of ImageSlime

## Contact 📧

For questions, issues, or suggestions, please open an issue on GitHub or contact the project maintainers.

---

**ImageSlime - Making image editing fun and accessible!** 🎨✨
