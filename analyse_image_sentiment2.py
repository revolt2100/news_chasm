import os
import json
import torch
from urllib.parse import urlparse
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from tqdm import tqdm

# ==========================================
# HELPER FUNCTION: MATCH FILENAMES
# ==========================================
def get_base_name(path_or_url):
    """Safely strips folders and double extensions (like .jpg.webp) to match names."""
    base = os.path.basename(urlparse(path_or_url).path)
    while True:
        stripped = False
        for ext in ['.webp', '.jpg', '.jpeg', '.png', '.bmp']:
            if base.lower().endswith(ext):
                base = base[:-len(ext)]
                stripped = True
        if not stripped:
            break
    return base.lower()

def main():
    # 1. Configuration
    base_dataset_file = "final_merged_holod_data2.json" # <--- Master JSON file
    output_results_file = "image_sentiment_results2.json"
    source_dirs = ["labeled_illustrations", "labeled_photos"]
    
    # 2. Find which images already have scores in the Master JSON
    processed_basenames = set()
    
    print(f"Reading master dataset: {base_dataset_file}...")
    try:
        with open(base_dataset_file, "r", encoding="utf-8") as f:
            main_data = json.load(f)
            
        for article in main_data:
            for img in article.get("Images", []):
                score = img.get("sentiment_score")
                url = img.get("url", "")
                
                # If it has a valid number score, we consider it "done"
                if score is not None and isinstance(score, (int, float)) and url:
                    processed_basenames.add(get_base_name(url))
                    
        print(f"Found {len(processed_basenames)} images that are already successfully analyzed.")
    except FileNotFoundError:
        print(f"❌ Could not find {base_dataset_file}. Please check the filename.")
        return

    # 3. Scan local directories for missing images
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    image_files_to_process = []
    
    for directory in source_dirs:
        if not os.path.isdir(directory):
            print(f"Warning: Directory '{directory}' not found. Skipping.")
            continue
            
        for f in os.listdir(directory):
            if os.path.splitext(f)[1].lower() in valid_extensions:
                base_name = get_base_name(f)
                
                # SMART FILTER: If the base name is already in our JSON with a score, skip it!
                if base_name in processed_basenames:
                    continue
                    
                full_path = os.path.join(directory, f)
                image_files_to_process.append((directory, f, full_path))
    
    if not image_files_to_process:
        print("\n✅ ALL images in your folders already have scores in the JSON!")
        print("You don't need to run this model anymore.")
        return

    print(f"\n🚀 Found {len(image_files_to_process)} missing images. Starting analysis...\n")

    # 4. Automatically use GPU, MPS, or CPU
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"Using device: {device.upper()}")

    # 5. Load CLIP model and processor
    print("Loading CLIP model...")
    model_id = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_id).to(device)
    processor = CLIPProcessor.from_pretrained(model_id)

    # 6. Prompts & Categories
    text_prompts = [
        "a news image with a positive, uplifting, or happy sentiment",
        "a news image with a negative, tragic, or angry sentiment",
        "a neutral, informational, or objective news image"
    ]
    categories = ["Positive", "Negative", "Neutral"]
    
    new_results = []

    # 7. Process missing images
    for directory, img_file, full_path in tqdm(image_files_to_process, desc="Analyzing Sentiment"):
        try:
            image = Image.open(full_path).convert("RGB")

            inputs = processor(
                text=text_prompts, 
                images=image, 
                return_tensors="pt", 
                padding=True
            ).to(device)

            with torch.no_grad():
                outputs = model(**inputs)
            
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1).cpu().numpy()[0]
            best_idx = probs.argmax()
            sentiment_score = float(probs[0]) - float(probs[1])
            
            new_results.append({
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
            new_results.append({
                "filename": img_file,
                "directory": directory,
                "path": full_path,
                "error": str(e)
            })

    # 8. Load any previous results so we don't overwrite them
    existing_results = []
    if os.path.exists(output_results_file):
        with open(output_results_file, "r", encoding="utf-8") as f:
            try:
                existing_results = json.load(f)
            except json.JSONDecodeError:
                pass
                
    all_results = existing_results + new_results

    # 9. Sort results
    def sort_key(item):
        if "error" in item:
            return float('-inf')
        return item.get("sentiment_score", 0)
    
    all_results.sort(key=sort_key, reverse=True)

    # 10. Save back to image_sentiment_results.json
    with open(output_results_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=4, ensure_ascii=False)
        
    print(f"\nDone! {len(new_results)} newly analyzed images saved to {output_results_file}.")
    print("👉 Next step: Run your 'Merge Script' again to inject these new scores into final_merged_holod_data.json!")

if __name__ == "__main__":
    main()