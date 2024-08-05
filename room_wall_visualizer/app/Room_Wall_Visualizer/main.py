'''
FastAPI part of the application
'''
# ----------------------------------------------------------------------
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import io
from PIL import Image
import os
import cv2
import numpy as np
import json
from utils.room_processing import *
from utils.texture_mapping import get_wall_corners, map_texture, load_texture, image_resize
from wall_segmentation.segmenation import wall_segmenting, build_model
from wall_estimation.estimation import wall_estimation
from warnings import filterwarnings
filterwarnings("ignore")

# ----------------------------------------------------------------------
IMG_FOLDER = os.path.join("static", "IMG")
DATA_FOLDER = os.path.join("static", "data")

ROOM_IMAGE = os.path.join(IMG_FOLDER, "room.jpg")
COLORED_ROOM_PATH = os.path.join(IMG_FOLDER, "colored_room.jpg")
TEXTURED_ROOM_PATH = os.path.join(IMG_FOLDER, "textured_room.jpg")
TEXTURE_PATH = os.path.join(IMG_FOLDER, "texture.jpg")
MASK_PATH = os.path.join(DATA_FOLDER, "image_mask.npy")
CORNERS_PATH = os.path.join(DATA_FOLDER, "corners_estimation.npy")
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
app = FastAPI()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Mount static files 
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load pretrained wall segmentation model
model = build_model()
# ----------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "room": ROOM_IMAGE})


@app.get("/redirect-to-texture")
async def redirect_to_texture(request: Request):
    return templates.TemplateResponse("applied_layout.html", {"request": request, "room": ROOM_IMAGE})


@app.post("/prediction")
async def predict_image_room(request: Request, file: UploadFile = File(...), button: str = Form(...)):
    try:
        contents = await file.read()
        op_img = Image.open(io.BytesIO(contents))
        op_img = np.asarray(op_img)

        if op_img.shape[0] > 600:
            op_img = image_resize(op_img, height=600)

        op_img = Image.fromarray(op_img)

        op_img.save(ROOM_IMAGE)
        op_img.save(COLORED_ROOM_PATH)
        op_img.save(TEXTURED_ROOM_PATH)

        path_image = os.path.abspath(ROOM_IMAGE)
        
        # start wall segmentation
        mask1 = wall_segmenting(model, path_image)
        
        # start wall estimation
        estimation_map = wall_estimation(path_image)
        
        # get coordinates of walls
        corners = get_wall_corners(estimation_map)

        # intersect two segmentation masks for getting somewhat more uniform result
        mask2 = np.full(mask1.shape, 0, dtype=np.uint8)

        for pts in corners:
            pts = np.array(pts)
            cv2.fillPoly(mask2, [pts], color=(255, 0, 0))

        mask2 = np.bool_(mask2)

        mask = mask1 & mask2

        with open(MASK_PATH, "wb") as f:
            np.save(f, mask)

        with open(CORNERS_PATH, "wb") as f:
            np.save(f, np.array(corners))
        
        if button == "texture":
            return RedirectResponse(url="/textured_room")

        return templates.TemplateResponse("result.html", {"request": request})

    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@app.get("/textured_room")
async def textured_room(request: Request):
    return templates.TemplateResponse("applied_texture.html", {"request": request, "new_room": TEXTURED_ROOM_PATH})


@app.post("/result_textured")
async def result_textured(file: UploadFile = File(None)):
    if file:
        contents = await file.read()
        op_img = Image.open(io.BytesIO(contents))
        op_img.save(TEXTURE_PATH)

    img = load_img(ROOM_IMAGE)

    with open(CORNERS_PATH, "rb") as f:
        corners = np.load(f)

    with open(MASK_PATH, "rb") as f:
        mask = np.load(f)

    texture = load_texture(TEXTURE_PATH, 6, 6)
    img_textured = map_texture(texture, img, corners, mask)
    out = brightness_transfer(img, img_textured, mask)

    save_image(out, TEXTURED_ROOM_PATH)

    return JSONResponse(content={"state": "success", "room_path": TEXTURED_ROOM_PATH})


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    rgb_tuple = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return rgb_tuple


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9090)
# @app.get("/")   
# def read_root():
#     return {"id": socket.gethostname()}