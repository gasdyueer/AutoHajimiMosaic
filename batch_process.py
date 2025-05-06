import argparse
import os
from pathlib import Path

from imagecodecs import imread, imwrite, imagefileext

from util import apply_mask, classify_image, load_models, segment_image, to_rgb, to_rgba


def process_images(input_folder, output_folder, pattern_image_path, head_image_path):
    input_folder = Path(input_folder)
    output_folder = Path(output_folder)

    classification_model, segmentation_model = load_models()
    names = segmentation_model.names

    pattern_image = to_rgba(imread(pattern_image_path))
    head_image = to_rgba(imread(head_image_path))

    support_ext = imagefileext()
    for file in input_folder.rglob("*"):
        if file.suffix[1:] in support_ext:
            image = to_rgb(imread(file))

            # Classify the image
            category = classify_image(image, classification_model)
            category_name = classification_model.names[category[0]]

            # Segment the image
            segmentation_results = segment_image(image, segmentation_model)
            try:
                masks = segmentation_results[0].masks.data.cpu().numpy()
                class_ids = segmentation_results[0].boxes.cls.cpu().numpy().astype(int)
            except AttributeError:
                if category_name in ['porn', 'hentai']:
                    print(f"Warning: {file} is classified as sensitive content, but no mask was found.")
                masks = []
                class_ids = []

            mask_options = [names[class_id] for class_id in class_ids]
            selected_masks = mask_options  # Automatically select all masks
            
            if selected_masks:
                image_with_fill = image.copy()
                for i, mask in enumerate(masks):
                    if mask_options[i] in selected_masks:
                        image_with_fill = apply_mask(image_with_fill, mask, pattern_image, head_image)

                # Save the processed image
                output_path = output_folder / file.relative_to(input_folder)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                imwrite(output_path, image_with_fill)
                print(f"Processed and saved: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch process images with YOLO models.")
    parser.add_argument("input_folder", type=str, help="Path to the input folder containing images.")
    parser.add_argument("output_folder", type=str, help="Path to the output folder to save processed images.")
    parser.add_argument("--pattern_image", type=str, default="assets/pattern.png", help="Path to the pattern image.")
    parser.add_argument("--head_image", type=str, default="assets/head.png", help="Path to the head image.")

    args = parser.parse_args()

    os.makedirs(args.output_folder, exist_ok=True)
    process_images(args.input_folder, args.output_folder, args.pattern_image, args.head_image)
