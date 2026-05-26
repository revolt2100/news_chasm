import json

# ==========================================
# CONFIGURATION
# ==========================================
# The file that currently has 1000 articles (but missing some images)
current_file_path = '3_holod_enriched_text.json' 

# The older file that contains your raw scraped data (with images)
older_file_path = 'filtered_text_holod_labeled.json'

# The final output file
output_file_path = 'image_rescued_holod_data.json'

print("Loading files...")
with open(current_file_path, 'r', encoding='utf-8') as f:
    current_data = json.load(f)
with open(older_file_path, 'r', encoding='utf-8') as f:
    older_data = json.load(f)

# ==========================================
# PREPARATION
# ==========================================
# 1. Create a quick lookup dictionary for the older data by URL
older_lookup = {article.get("URL"): article for article in older_data if article.get("URL")}

# 2. Get a list of URLs currently in our dataset so we don't accidentally duplicate them
current_urls = set(article.get("URL") for article in current_data if article.get("URL"))

# 3. Build a "Spare Pool" of unused, image-rich articles from the older file
spare_pool = [
    article for article in older_data 
    if article.get("URL") not in current_urls and len(article.get("Images", [])) > 0
]

print(f"Built a spare pool of {len(spare_pool)} unused articles with images.")

# ==========================================
# PROCESSING
# ==========================================
updated_dataset = []

stats = {
    "kept_original": 0,
    "rescued_images_only": 0,
    "replaced_entire_article": 0,
    "failed_no_spares_left": 0
}

print("Scanning and repairing articles...")

for article in current_data:
    url = article.get("URL")
    images = article.get("Images", [])
    
    # TIER 1: Article is already fine and has images
    if len(images) > 0:
        updated_dataset.append(article)
        stats["kept_original"] += 1
        continue

    # TIER 2: Article has NO images. Let's try to rescue the images from the older file.
    older_version = older_lookup.get(url, {})
    older_images = older_version.get("Images", [])
    
    if len(older_images) > 0:
        # Success! Copy the images over.
        article["Images"] = older_images
        updated_dataset.append(article)
        stats["rescued_images_only"] += 1
        continue

    # TIER 3: The article is fundamentally image-less. Replace it entirely.
    if len(spare_pool) > 0:
        # Take the first available article from our spare pool
        replacement_article = spare_pool.pop(0) 
        updated_dataset.append(replacement_article)
        stats["replaced_entire_article"] += 1
    else:
        # Very rare: We ran out of spare articles! Just keep the image-less one.
        updated_dataset.append(article)
        stats["failed_no_spares_left"] += 1

# ==========================================
# SAVE & REPORT
# ==========================================
with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(updated_dataset, f, ensure_ascii=False, indent=2)

print("\n" + "="*40)
print("             REPAIR REPORT")
print("="*40)
print(f"1. Articles perfectly fine:     {stats['kept_original']}")
print(f"2. Missing images rescued:      {stats['rescued_images_only']}")
print(f"3. Entire articles replaced:    {stats['replaced_entire_article']}")
if stats["failed_no_spares_left"] > 0:
    print(f"⚠️ Failed (Ran out of spares): {stats['failed_no_spares_left']}")
print("-" * 40)
print(f"FINAL DATASET SIZE:             {len(updated_dataset)}")
print("="*40)
print(f"\nSaved to '{output_file_path}'")