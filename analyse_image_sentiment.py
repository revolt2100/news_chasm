import os
import json
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from tqdm import tqdm

def main():
    # 1. Automatically use GPU (Nvidia), MPS (Mac), or fallback to CPU
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"Using device: {device.upper()}")

    # 2. Load CLIP model and processor
    print("Loading CLIP model...")
    model_id = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_id).to(device)
    processor = CLIPProcessor.from_pretrained(model_id)  # fixed: added model_id

    # 3. Define the text prompts for Zero-Shot Classification
    text_prompts = [
        "a news image with a positive, uplifting, or happy sentiment",
        "a news image with a negative, tragic, or angry sentiment",
        "a neutral, informational, or objective news image"
    ]
    categories = ["Positive", "Negative", "Neutral"]

    # 4. Find all images in the two child directories
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    source_dirs = ["labeled_illustrations", "labeled_photos"]
    
    image_files = []  # tuples of (directory, filename, full_path)
    
    for directory in source_dirs:
        if not os.path.isdir(directory):
            print(f"Warning: Directory '{directory}' not found. Skipping.")
            continue
            
        for f in os.listdir(directory):
            if os.path.splitext(f)[1].lower() in valid_extensions:
                full_path = os.path.join(directory, f)
                image_files.append((directory, f, full_path))
    
    if not image_files:
        print("No images found in labeled_illustrations or labeled_photos.")
        return

    print(f"Found {len(image_files)} images. Starting analysis...")
    
    results = []

    # 5. Process images with a progress bar
    for directory, img_file, full_path in tqdm(image_files, desc="Analyzing Sentiment"):
        try:
            # Open image and ensure it has 3 color channels (RGB)
            image = Image.open(full_path).convert("RGB")

            # Prepare inputs
            inputs = processor(
                text=text_prompts, 
                images=image, 
                return_tensors="pt", 
                padding=True
            ).to(device)

            # Run through the model (no_grad saves memory/speeds things up)
            with torch.no_grad():
                outputs = model(**inputs)
            
            # Get image-text similarity scores and convert to percentages (softmax)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1).cpu().numpy()[0]
            
            # Find the highest scoring category
            best_idx = probs.argmax()
            
            # Sentiment score for sorting: positive_prob - negative_prob
            # Range: -1.0 (most negative) to +1.0 (most positive)
            sentiment_score = float(probs[0]) - float(probs[1])
            
            results.append({
                "filename": img_file,
                "directory": directory,
                "path": full_path,
                "sentiment": categories[best_idx],
                "confidence_score": float(probs[best_idx]),
                "sentiment_score": round(sentiment_score, 6),
                "all_scores": {
                    categories[i]: round(float(probs[i]), 4) for i in range(len(categories))
                }
            })

        except Exception as e:
            # Catch corrupted images so the script doesn't stop halfway through
            results.append({
                "filename": img_file,
                "directory": directory,
                "path": full_path,
                "error": str(e)
            })

    # 6. Sort results: most positive on top, most negative last
    # Errors sink to the bottom since they have no sentiment_score
    def sort_key(item):
        if "error" in item:
            return float('-inf')  # forces errors to the end when reverse=True
        return item.get("sentiment_score", 0)
    
    results.sort(key=sort_key, reverse=True)

    # 7. Save results to JSON
    output_file = "image_sentiment_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    print(f"\nDone! Results saved to {output_file}")
    print(f"Total processed: {len(results)}")

if __name__ == "__main__":
    main()