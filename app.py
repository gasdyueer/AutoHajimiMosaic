import streamlit as st
from PIL import Image
import io
from util import load_models, classify_image, segment_image, apply_mask

classification_model, segmentation_model = load_models()
names = segmentation_model.names

def main():
    st.title("🐱自动哈基米打码机")
    st.write("上传一张图片，哈基米会自动识别区域并且覆盖上去，你可以选择不遮挡一部分，然后就可以下载下来送给朋友了！[Source Code](https://github.com/frinkleko/AutoHajimiMosaic)")

    uploaded_file = st.file_uploader("Upload an image...", type=["jpg", "jpeg", "png", "bmp", "webp"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)

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
                st.warning("是色图！但是哈基米不知道遮哪里。坏😭")
            masks = []
            class_ids = []

        mask_options = [names[class_id] for class_id in class_ids]
        selected_masks = st.multiselect("Select regions to mask", mask_options, default=mask_options)

        pattern_image = Image.open("assets/pattern.png")
        default_head_image = Image.open("assets/head.png").convert("RGBA")

        # Option to upload a custom head image
        use_custom_head = st.checkbox("使用你自己的哈基米")
        if use_custom_head:
            custom_head_file = st.file_uploader("上传你的哈基米(推荐PNG with transparency)...", type=["png", "jpg", "jpeg"])
            if custom_head_file is not None:
                head_image = Image.open(custom_head_file).convert("RGBA")
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

            # Convert image to bytes for download
            buf = io.BytesIO()
            image_with_fill.save(buf, format="PNG")
            byte_im = buf.getvalue()

            # Download button
            st.download_button(
                label="下载",
                data=byte_im,
                file_name="edited_image.png",
                mime="image/png"
            )


if __name__ == "__main__":
    main()
