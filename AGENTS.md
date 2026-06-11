## Project ImageSlime
- ImageSlime is an image segmenter to remove backgrounds, select/segment objects, mix segmented objects and content from multiple images and download the result to make memes, edit out unwanted objects and other quick image editing
- The interface runs off a browser, with minimal latency
- The background server uses python host and do the segmentation

### Technical Details
- We will use Meta's Segment Anything Model also called SAM (https://github.com/facebookresearch/segment-anything)
- The goal is to enable the user to click to select or draw a boundary around an object or background
- Use the SAM API to learn how to implement segmentation and get image masks


#### Segmentation Embeddings
- Use SAM3 model in python
- Use embeddings of images calculated in the backend to make the user experience in the browser fast
- Allow the user to select one or more points or bounding boxes
- These points are used on the precomputed embeddings to get masks 

#### Interface and User Abilities
- Once the image object is selected, the user can do common image operations like drag it over other images in the tab, delete the object, rotate it or enlarge it
- There are multiple layers in the web interface which act as the images. The user can right click and move an image, or selected/highlighted object one layer back or front; or move to front or back entirely
- Provide options to user to download the end result

### Programming Etiquette
- Keep things simple, silly
- Avoid complexity
- Functional where possible
- make code easy to understand. Make the code verbose rather than terse and complex

### uv
use `uv add torch` to install torch package for example
use `uv run main.py` to run main.py

## RESEARCH YOURSELF AND FIGURE OUT THE BEST WAY TO ADD FUNCTIONALITY
- Use web search and API search to figure out how to implement this project
- Present best options and allow me to pick and choose