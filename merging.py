import json
import os
from urllib.parse import urlparse

# ==========================================
# CONFIGURATION
# ==========================================
# 1. The file containing the results from your CLIP image model
sentiment_source_file = 'image_sentiment_results.json'

# 2. Your main dataset file that needs the scores injected
main_dataset_file = 'final_merged_holod_data.json'

# 3. The final output file
output_file = 'final_merged_holod_data2.json'

# ==========================================
# HELPER FUNCTION: MATCH FILENAMES
# ==========================================
def get_base_name(path_or_url):
    """
    Converts 'https://holod.media/.../image_name.jpg.webp' AND 'image_name.jpg' 
    both into just 'image_name' so they can be matched perfectly.
    """
    # Get just the file part from the end of the URL or path
    base = os.path.basename(urlparse(path_or_url).path)
    
    # Strip common extensions
    for ext in ['.webp', '.jpg', '.jpeg', '.png', '.bmp']:
        if base.lower().endswith(ext):
            base = base[:-len(ext)]
    return base.lower()

# ==========================================
# PROCESSING
# ==========================================
print("Loading files...")
try:
    with open(sentiment_source_file, 'r', encoding='utf-8') as f:
        sentiment_data = json.load(f)
except FileNotFoundError:
    print(f"❌ Could not find {sentiment_source_file}. Run your image model first!")
    exit()

with open(main_dataset_file, 'r', encoding='utf-8') as f:
    main_data = json.load(f)

# 1. Build a lookup dictionary from the CLIP sentiment results
print("Building lookup dictionary...")
sentiment_lookup = {}
for item in sentiment_data:
    filename = item.get("filename", "")
    if filename:
        base_name = get_base_name(filename)
        sentiment_lookup[base_name] = item

# Counters
total_images_checked = 0
successfully_updated = 0
missing_images = []

# 2. Inject the data into the main dataset
print("Merging data...")
for article in main_data:
    images = article.get("Images", [])
    
    for img in images:
        total_images_checked += 1
        url = img.get("url", "")
        
        if not url:
            continue
            
        base_name = get_base_name(url)
        
        # Look for the match in our sentiment dictionary
        matching_sentiment = sentiment_lookup.get(base_name)
        
        if matching_sentiment and "sentiment_score" in matching_sentiment:
            # Match found! Copy the data over
            img["sentiment"] = matching_sentiment.get("sentiment")
            img["confidence_score"] = matching_sentiment.get("confidence_score")
            img["sentiment_score"] = matching_sentiment.get("sentiment_score")
            img["all_scores"] = matching_sentiment.get("all_scores")
            
            successfully_updated += 1
        else:
            # No match found in the CLIP results
            missing_images.append(url)

# 3. Save the merged dataset
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(main_data, f, ensure_ascii=False, indent=2)

# ==========================================
# REPORT
# ==========================================
print("\n" + "="*40)
print("             MERGE REPORT")
print("="*40)
print(f"Total images in dataset:  {total_images_checked}")
print(f"Scores successfully copied: {successfully_updated}")
print("-" * 40)

if len(missing_images) == 0:
    print("✅ PERFECT MATCH! All images have sentiment scores.")
    print("You DO NOT need to run the sentiment analysis again.")
else:
    print(f"⚠️  MISSING DATA: {len(missing_images)} images had no scores to copy.")
    print("You NEED to run the sentiment analysis script again on these images:")
    print("-" * 40)
    # Print up to 10 missing URLs so as not to spam your terminal
    for missing_url in missing_images[:10]:
        print(f" - {missing_url}")
    
    if len(missing_images) > 10:
        print(f"   ... and {len(missing_images) - 10} more.")

print("="*40)
print(f"\nSaved updated dataset to '{output_file}'")