import io

import cv2
import streamlit as st
from imagecodecs import imagefileext, imread, imwrite

from util import apply_mask, classify_image, load_models, segment_image, to_rgb, to_rgba

classification_model, segmentation_model = load_models()
names = segmentation_model.names

def main():
    support_ext = imagefileext()
    st.title("🐱自动哈基米打码机")
    st.write("上传一张图片，哈基米会自动识别区域并且覆盖上去，你可以选择不遮挡一部分，然后就可以下载下来送给朋友了！[Source Code](https://github.com/frinkleko/AutoHajimiMosaic)")

    uploaded_file = st.file_uploader("Upload an image", type=None)

    # Check the file extension manually
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension in support_ext:
            pass
        else:
            st.error("Unsupported file format.")
    
    if uploaded_file is not None:
        image = to_rgb(imread(uploaded_file.read()))
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Classify the image
        category = classify_image(image_bgr, classification_model)
        category_name = classification_model.names[category[0]]

        # Segment the image
        segmentation_results = segment_image(image_bgr, segmentation_model)
        try:
            masks = segmentation_results[0].masks.data.cpu().numpy()
            class_ids = segmentation_results[0].boxes.cls.cpu().numpy().astype(int)
        except AttributeError:
            if category_name in ['porn', 'hentai']:
                st.warning("是色图！但是哈基米不知道遮哪里。坏😭")
            masks = []
            class_ids = []

        mask_options = [names[class_id] for class_id in class_ids]
        selected_masks = st.multiselect("Select regions to mask", mask_options, default=mask_options)

        pattern_image = imread("assets/pattern.png")
        default_head_image = to_rgba(imread("assets/head.png"))

        # Option to upload a custom head image
        use_custom_head = st.checkbox("使用你自己的哈基米")
        if use_custom_head:
            custom_head_file = st.file_uploader("上传你的哈基米(推荐PNG with transparency)...", type=["png", "jpg", "jpeg"])
            if custom_head_file is not None:
                head_image = to_rgba(imread(custom_head_file.read()))
            else:
                head_image = default_head_image
        else:
            head_image = default_head_image

        if selected_masks:
            image_with_fill = image.copy()
            for i, mask in enumerate(masks):
                if mask_options[i] in selected_masks:
                    image_with_fill = apply_mask(image_with_fill, mask, pattern_image, head_image)

            # Layout adjustment
            col1, col2 = st.columns(2, gap="small")
            with col1:
                st.image(image, caption="原图", use_container_width=True)
            with col2:
                st.image(image_with_fill, caption="哈基米图", use_container_width=True)

            # Format selection and download button
            col1, col2 = st.columns([1, 2])
            with col1:
                format_option = st.radio("选择下载格式", ("png", "jpeg"), index=0)
            with col2:
                # Convert image to bytes for download based on selected format
                buf = io.BytesIO()
                imwrite(buf, image_with_fill, codec=format_option)
                byte_im = buf.getvalue()

                st.download_button(
                    label="下载",
                    data=byte_im,
                    file_name=f"edited_image.{format_option}",
                    mime=f"image/{format_option}"
                )

if __name__ == "__main__":
    main()
