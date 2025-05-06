import gradio as gr
from PIL import Image
from util import load_models, classify_image, segment_image, apply_mask

classification_model, segmentation_model = load_models()
names = segmentation_model.names

def process_image(uploaded_file, use_custom_head, custom_head_file=None):
    image = Image.open(uploaded_file)

    category = classify_image(image, classification_model)
    category_name = classification_model.names[category[0]]

    segmentation_results = segment_image(image, segmentation_model)
    try:
        masks = segmentation_results[0].masks.data.cpu().numpy()
        class_ids = segmentation_results[0].boxes.cls.cpu().numpy().astype(int)
    except AttributeError:
        if category_name in ['porn', 'hentai']:
            return "是色图！但是哈基米不知道遮哪里。坏😭", None
        masks = []
        class_ids = []

    mask_options = [names[class_id] for class_id in class_ids]

    pattern_image = Image.open("assets/pattern.png")
    default_head_image = Image.open("assets/head.png").convert("RGBA")

    if use_custom_head and custom_head_file is not None:
        head_image = custom_head_file.convert("RGBA")
    else:
        head_image = default_head_image

    image_with_fill = image.copy()
    for i, mask in enumerate(masks):
        if mask_options[i] in mask_options:
            image_with_fill = apply_mask(image_with_fill, mask, pattern_image, head_image)

    return image, image_with_fill

def toggle_custom_head(use_custom_head):
    return gr.update(visible=use_custom_head)

with gr.Blocks() as iface:
    gr.Markdown("## 🐱自动哈基米打码机\n上传一张图片，哈基米会自动识别区域并且覆盖上去，你可以选择不遮挡一部分，然后就可以下载下来送给朋友了！[Source Code](https://github.com/frinkleko/AutoHajimiMosaic)")

    uploaded_file = gr.File(label="上传图片")
    use_custom_head = gr.Checkbox(label="使用你自己的哈基米", value=False)
    custom_head_file = gr.Image(type="pil", label="上传你的哈基米(推荐PNG with transparency)", visible=False)

    use_custom_head.change(toggle_custom_head, inputs=use_custom_head, outputs=custom_head_file)

    submit_btn = gr.Button("Submit")
    
    with gr.Row():
        original_output = gr.Image(type="pil", label="原图")
        mosaic_output = gr.Image(type="pil", label="哈基米图")

    submit_btn.click(
        process_image,
        inputs=[uploaded_file, use_custom_head, custom_head_file],
        outputs=[original_output, mosaic_output]
    )

iface.launch(share=True)
