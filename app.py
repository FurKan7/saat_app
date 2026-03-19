import time
from dataclasses import dataclass
from typing import List, Tuple
#import spaces
import gradio as gr
import torch
from PIL import Image
from transformers import (
    AutoConfig,
    AutoProcessor,
    AutoModelForZeroShotObjectDetection,
)

def extract_model_short_name(model_id: str) -> str:
    return model_id.split("/")[-1].replace("-", " ").replace("_", " ")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

@dataclass
class ZSDetBundle:
    model_id: str
    model_name: str
    processor: AutoProcessor
    model: AutoModelForZeroShotObjectDetection

# LLMDet
model_llmdet_id = "iSEE-Laboratory/llmdet_tiny"
processor_llmdet = AutoProcessor.from_pretrained(model_llmdet_id)
config_llmdet = AutoConfig.from_pretrained(model_llmdet_id)
config_llmdet.tie_word_embeddings = False
model_llmdet = AutoModelForZeroShotObjectDetection.from_pretrained(model_llmdet_id, config=config_llmdet)
bundle_llmdet = ZSDetBundle(
    model_id=model_llmdet_id,
    model_name=extract_model_short_name(model_llmdet_id),
    processor=processor_llmdet,
    model=model_llmdet,
)

# MM GroundingDINO
model_mm_grounding_id = "rziga/mm_grounding_dino_tiny_o365v1_goldg"
processor_mm_grounding = AutoProcessor.from_pretrained(model_mm_grounding_id)
config_mm_grounding = AutoConfig.from_pretrained(model_mm_grounding_id)
config_mm_grounding.tie_word_embeddings = False
model_mm_grounding = AutoModelForZeroShotObjectDetection.from_pretrained(model_mm_grounding_id, config=config_mm_grounding)
bundle_mm_grounding = ZSDetBundle(
    model_id=model_mm_grounding_id,
    model_name=extract_model_short_name(model_mm_grounding_id),
    processor=processor_mm_grounding,
    model=model_mm_grounding,
)
#@spaces.GPU
def detect(
    bundle: ZSDetBundle,
    image: Image.Image,
    prompts: List[str],
    threshold: float,
) -> Tuple[List[Tuple[Tuple[int, int, int, int], str]], str]:
    t0 = time.perf_counter()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    texts = [prompts]
    inputs = bundle.processor(images=image, text=texts, return_tensors="pt").to(device)
    model = bundle.model.to(device).eval()

    with torch.inference_mode():
        outputs = model(**inputs)

    results = bundle.processor.post_process_grounded_object_detection(
        outputs, threshold=threshold, target_sizes=[image.size[::-1]], text_labels=texts,
    )[0]

    annotations = []
    for box, score, label_name in zip(results["boxes"], results["scores"], results["text_labels"]):
        if float(score) < threshold:
            continue
        xmin, ymin, xmax, ymax = map(lambda v: int(v), box.tolist())
        annotations.append(((xmin, ymin, xmax, ymax), f"{label_name} {float(score):.2f}"))

    elapsed_ms = (time.perf_counter() - t0) * 1000
    time_taken = f"**Inference time ({bundle.model_name}):** {elapsed_ms:.0f} ms"
    return annotations, time_taken

def parse_prompts(prompts_str: str) -> List[str]:
    return [p.strip() for p in prompts_str.split(",") if p.strip()]

def run_detection(
    image: Image.Image,
    prompts_str: str,
    threshold_llm: float,
    threshold_mm: float,
):
    prompts = parse_prompts(prompts_str)

    ann_llm, time_llm = detect(bundle_llmdet, image, prompts, threshold_llm)
    ann_mm, time_mm = detect(bundle_mm_grounding, image, prompts, threshold_mm)

    return (
        (image, ann_llm), time_llm,
        (image, ann_mm), time_mm,
    )

description_md = """
# Zero-Shot Object Detection Arena

Compare **two zero-shot object detectors** on the same image + prompts.  
Upload an image (or pick an example), add **comma-separated prompts**, tweak per-model **thresholds**, and hit **Detect**.

**Models**
- LLMDet Tiny — [`iSEE-Laboratory/llmdet_tiny`](https://huggingface.co/iSEE-Laboratory/llmdet_tiny)
- MM GroundingDINO Tiny O365v1 GoldG — [`rziga/mm_grounding_dino_tiny_o365v1_goldg`](https://huggingface.co/rziga/mm_grounding_dino_tiny_o365v1_goldg)
"""

with gr.Blocks() as app:
    gr.Markdown(description_md)

    with gr.Row():
        with gr.Column(scale=1):
            image = gr.Image(type="pil", label="Upload an image", height=400)
            prompts = gr.Textbox(
                label="Prompts (comma-separated)",
                value="a watch, brand text",
                placeholder="e.g., a cat, a remote control",
            )
            with gr.Accordion("Per-model confidence thresholds", open=True):
                threshold_llm = gr.Slider(label=f"Threshold — {bundle_llmdet.model_name}", minimum=0.0, maximum=1.0, value=0.3)
                threshold_mm = gr.Slider(label=f"Threshold — {bundle_mm_grounding.model_name}", minimum=0.0, maximum=1.0, value=0.3)
            generate_btn = gr.Button(value="Detect")

        with gr.Row():
            with gr.Column(scale=2):
                output_image_llm = gr.AnnotatedImage(label=f"Annotated — {bundle_llmdet.model_name}", height=400)
                output_time_llm = gr.Markdown()
            with gr.Column(scale=2):
                output_image_mm = gr.AnnotatedImage(label=f"Annotated — {bundle_mm_grounding.model_name}", height=400)
                output_time_mm = gr.Markdown()

    gr.Markdown("### Examples")
    example_data = [
        ["http://images.cocodataset.org/val2017/000000039769.jpg", "a cat, a remote control", 0.30, 0.30],
        ["http://images.cocodataset.org/val2017/000000000139.jpg", "a person, a tv, a remote", 0.35, 0.30],
    ]

    gr.Examples(
        examples=example_data,
        inputs=[image, prompts, threshold_llm, threshold_mm],
        label="Click an example to populate the inputs",
    )

    inputs = [image, prompts, threshold_llm, threshold_mm]
    outputs = [
        output_image_llm, output_time_llm,
        output_image_mm, output_time_mm,
    ]
    generate_btn.click(fn=run_detection, inputs=inputs, outputs=outputs)
    image.upload(fn=run_detection, inputs=inputs, outputs=outputs)

app.launch()
