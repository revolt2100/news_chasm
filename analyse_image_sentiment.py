import json
import torch
import requests
from io import BytesIO
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from tqdm import tqdm

# ==========================================
# CONFIGURATION
# ==========================================
input_json_file = "AGAINholod_enriched3.json" # Your master file
output_json_file = "final.json" # New file so we don't overwrite the original if it crashes

# Pretend to be a web browser so the website doesn't block the image download
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def main():
    # 1. Load the Dataset
    print(f"Reading dataset: {input_json_file}...")
    try:
        with open(input_json_file, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print(f"❌ Could not find {input_json_file}. Please check the filename.")
        return

    # 2. Build a hit-list of images that need processing
    images_to_process = []
    
    for article_idx, article in enumerate(dataset):
        for img_idx, img in enumerate(article.get("Images", [])):
            score = img.get("sentiment_score")
            url = img.get("url")
            
            # If there's a URL, but no valid score, add it to our queue
            if url and not isinstance(score, (int, float)):
                # We save the indices so we can inject the data directly back into the dataset!
                images_to_process.append({
                    "article_idx": article_idx,
                    "img_idx": img_idx,
                    "url": url
                })
                
    print(f"🎯 Found {len(images_to_process)} images missing sentiment scores.")

    if not images_to_process:
        print("\n✅ All images in your JSON already have scores! You don't need to run this.")
        return

    # 3. Setup Hardware & Model
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"\nUsing device: {device.upper()}")

    print("Loading CLIP model...")
    model_id = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_id).to(device)
    processor = CLIPProcessor.from_pretrained(model_id)

    # 4. Prompts & Categories
    text_prompts = [
        "a news image with a positive, uplifting, or happy sentiment",
        "a news image with a negative, tragic, or angry sentiment",
        "a neutral, informational, or objective news image"
    ]
    categories = ["Positive", "Negative", "Neutral"]
    
    success_count = 0
    fail_count = 0

    # 5. Process the images over the internet
    for task in tqdm(images_to_process, desc="Analyzing Online Images"):
        url = task["url"]
        
        try:
            # Download the image into memory
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status() # Check for 404 or connection errors
            
            # Open it with PIL directly from RAM
            image = Image.open(BytesIO(response.content)).convert("RGB")

            # Run CLIP
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
            
            # Inject directly into our master dataset dictionary!
            target_img_dict = dataset[task["article_idx"]]["Images"][task["img_idx"]]
            target_img_dict["sentiment"] = categories[best_idx]
            target_img_dict["confidence_score"] = float(probs[best_idx])
            target_img_dict["sentiment_score"] = round(sentiment_score, 6)
            target_img_dict["all_scores"] = {
                categories[i]: round(float(probs[i]), 4) for i in range(len(categories))
            }
            
            success_count += 1

        except Exception as e:
            # If the link is broken or the image is corrupted, just note the error and move on
            target_img_dict = dataset[task["article_idx"]]["Images"][task["img_idx"]]
            target_img_dict["sentiment_error"] = str(e)
            fail_count += 1

    # 6. Save the completed dataset!
    with open(output_json_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
        
    print("\n" + "="*40)
    print("             RESULTS REPORT")
    print("="*40)
    print(f"Successfully downloaded and scored: {success_count}")
    print(f"Failed (Broken URLs or connection): {fail_count}")
    print("-" * 40)
    print(f"Fully updated dataset saved to '{output_json_file}'")
    print("You DO NOT need to run the merge script!")

if __name__ == "__main__":
    main()