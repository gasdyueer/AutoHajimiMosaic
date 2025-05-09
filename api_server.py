from fastapi import FastAPI, UploadFile, File
from pathlib import Path
import cv2
from imagecodecs import imread, imwrite
from util import apply_mask, classify_image, load_models, segment_image, to_rgb, to_rgba

app = FastAPI()

@app.post("/process/")
async def process_images(files: list[UploadFile], pattern_image: UploadFile = None, head_image: UploadFile = None):
    classification_model, segmentation_model = load_models()
    names = segmentation_model.names

    # Load default images if not provided
    default_pattern_image = to_rgba(imread("assets/pattern.png"))
    default_head_image = to_rgba(imread("assets/head.png"))

    pattern_image_data = to_rgba(imread(pattern_image.file.read())) if pattern_image else default_pattern_image
    head_image_data = to_rgba(imread(head_image.file.read())) if head_image else default_head_image

    processed_images = []

    for file in files:
        image = to_rgb(imread(file.file.read()))
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        category = classify_image(image_bgr, classification_model)
        category_name = classification_model.names[category[0]]

        segmentation_results = segment_image(image_bgr, segmentation_model)
        masks = segmentation_results[0].masks.data.cpu().numpy() if hasattr(segmentation_results[0], 'masks') else []
        class_ids = segmentation_results[0].boxes.cls.cpu().numpy().astype(int) if hasattr(segmentation_results[0], 'boxes') else []

        mask_options = [names[class_id] for class_id in class_ids]

        if mask_options:
            image_with_fill = image.copy()
            for i, mask in enumerate(masks):
                if mask_options[i] in mask_options:
                    image_with_fill = apply_mask(image_with_fill, mask, pattern_image_data, head_image_data)

            processed_images.append(imwrite(image_with_fill))

    return {"processed_images": processed_images}
