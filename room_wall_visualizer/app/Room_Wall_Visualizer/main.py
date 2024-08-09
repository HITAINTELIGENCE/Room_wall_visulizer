from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import io
from PIL import Image
import os
import cv2
import numpy as np
import uuid
import time
from utils.room_processing import *
from utils.texture_mapping import get_wall_corners, map_texture, load_texture, image_resize
from wall_segmentation.segmenation import wall_segmenting, build_model
from wall_estimation.estimation import wall_estimation
from warnings import filterwarnings

filterwarnings("ignore")

# ----------------------------------------------------------------------
IMG_FOLDER = 'static/IMG/'
DATA_FOLDER = 'static/data/'

from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware


class ForwardedProtoMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.headers.get("x-forwarded-proto") == "https":
            request.scope["scheme"] = "https"
        response = await call_next(request)
        return response

app = FastAPI()
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(ForwardedProtoMiddleware)

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Mount static files 
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Load pretrained wall segmentation model
model = build_model()

# Store filenames globally for now (Consider a better state management)
file_paths = {}

# ----------------------------------------------------------------------

# Unique filename generator
def generate_unique_filename(base_name, extension=".jpg"):
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())
    return f"{base_name}_{timestamp}_{unique_id}{extension}"

# --------------------------START HTML PAGES----------------------------
@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/room_visualization_index")
async def room_visualization_index(request: Request):
    texture_images = [f for f in os.listdir('static/test_images/textures') if f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    return templates.TemplateResponse("room_visualization_index.html", {"request": request, 
                                                                        "room": None, 
                                                                        "images": texture_images})

# --------------------------END HTML PAGES----------------------------
@app.post("/room_visualization_prediction")
async def predict_image_room(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        with Image.open(io.BytesIO(contents)) as op_img:
            op_img = np.asarray(op_img)

            if op_img.shape[0] > 600:
                op_img = image_resize(op_img, height=600)

            op_img = Image.fromarray(op_img)

            # Generate unique filenames
            unique_room_image = IMG_FOLDER+generate_unique_filename("room", ".jpg")
            unique_textured_room_path = IMG_FOLDER+generate_unique_filename("textured_room", ".jpg")
            unique_mask_path = DATA_FOLDER+generate_unique_filename("image_mask", ".npy")
            unique_corners_path = DATA_FOLDER+generate_unique_filename("corners_estimation", ".npy")

            # Save the uploaded image and a copy for processing
            op_img.save(unique_room_image)
            op_img.save(unique_textured_room_path)

            # Store file paths globally (you can refactor this to use better state management)
            file_paths.update({
                "room_image": unique_room_image,
                "textured_room_path": unique_textured_room_path,
                "mask_path": unique_mask_path,
                "corners_path": unique_corners_path,
            })

        # Perform wall segmentation and estimation
        mask1 = wall_segmenting(model, unique_room_image)
        estimation_map = wall_estimation(unique_room_image)

        # Get wall corners and create the final mask
        corners = get_wall_corners(estimation_map)
        mask2 = np.zeros(mask1.shape, dtype=np.uint8)
        for pts in corners:
            cv2.fillPoly(mask2, [np.array(pts)], color=(255, 0, 0))

        mask = mask1 & np.bool_(mask2)

        # Save the mask and corners data
        np.save(unique_mask_path, mask)
        np.save(unique_corners_path, np.array(corners))
        
        return {"state": "success", "room_image": unique_room_image, "textured_room_path": unique_textured_room_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/apply_texture/{image}")
async def apply_texture(image: str):
    try:
        # Load the previously stored paths
        room_image = file_paths.get("room_image")
        mask_path = file_paths.get("mask_path")
        corners_path = file_paths.get("corners_path")
        textured_room_path = file_paths.get("textured_room_path")

        if not all([room_image, mask_path, corners_path, textured_room_path]):
            raise HTTPException(status_code=400, detail="Required file paths are missing.")

        img = load_img(room_image)

        # Load computed vertices of a wall and segmentation mask of room walls
        corners = np.load(corners_path, allow_pickle=True)
        mask = np.load(mask_path, allow_pickle=True)

        # Load and apply the selected texture
        texture_path = os.path.join("static", "test_images", "textures", image)
        texture = load_texture(texture_path, 6, 6)
        img_textured = map_texture(texture, img, corners, mask)

        # Transfer shadows and highlights from the original image
        out = brightness_transfer(img, img_textured, mask)

        # Save the processed image
        save_image(out, textured_room_path)

        return JSONResponse(content={"state": "success", "room_path": textured_room_path})

    except Exception as e:
        return JSONResponse(content={"state": "error", "message": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9090)
