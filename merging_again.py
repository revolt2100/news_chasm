import json

# ==========================================
# CONFIGURATION
# ==========================================
# The older file containing the raw labeled data
source_file = 'filtered_text_holod_labeled.json'

# Your current master file
target_file = 'holod_data_with_illustrations2.json'

# The new output file
output_file = 'holod_data_with_illustrations4.json'

# How many articles to extract
MAX_ARTICLES_TO_ADD = 500

# ==========================================
# PROCESSING
# ==========================================
print("Loading files...")
with open(source_file, 'r', encoding='utf-8') as f:
    source_data = json.load(f)

with open(target_file, 'r', encoding='utf-8') as f:
    target_data = json.load(f)

# 1. Get a list of URLs currently in our master dataset so we don't add duplicates
existing_urls = set(article.get("URL") for article in target_data if article.get("URL"))

# 2. Scan the older file for articles with AT LEAST ONE illustration
articles_to_add = []

print("Scanning for articles containing at least one illustration...")
for article in source_data:
    url = article.get("URL")
    images = article.get("Images", [])
    
    # Skip if it's already in our master dataset
    if url in existing_urls:
        continue
        
    # We only want articles that actually have images...
    if len(images) > 0:
        # TWEAKED: any() returns True if AT LEAST ONE image meets the condition
        has_illustration = any(img.get("Is illustration") == 1 for img in images)
        
        if has_illustration:
            articles_to_add.append(article)
            
            # Stop searching if we hit our target number
            if len(articles_to_add) >= MAX_ARTICLES_TO_ADD:
                break

# 3. Merge the new articles into the master dataset
updated_dataset = target_data + articles_to_add

# 4. Save the results
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(updated_dataset, f, ensure_ascii=False, indent=2)

# ==========================================
# REPORT
# ==========================================
print("\n" + "="*40)
print("             EXTRACTION REPORT")
print("="*40)
print(f"Target limit:                {MAX_ARTICLES_TO_ADD}")
print(f"Found and extracted:         {len(articles_to_add)}")
print("-" * 40)
print(f"Previous master dataset size: {len(target_data)}")
print(f"NEW MASTER DATASET SIZE:      {len(updated_dataset)}")
print("="*40)
print(f"\nSaved updated dataset to '{output_file}'")