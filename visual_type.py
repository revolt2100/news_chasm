import json

# 1. Configuration: File names
input_filename = 'transformed_LR_modality.json'  # Put your current JSON file name here
output_filename = 'visual_types_added.json'      # The new file that will be created

print(f"Loading dataset from '{input_filename}'...")
with open(input_filename, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# Counters to show you a summary at the end
counts = {
    "Photos-only": 0,
    "Illustration-based": 0,
    "Mixed": 0,
    "No Images": 0
}

# 2. Process each article
for article in dataset:
    images = article.get("Images", [])
    
    if not images:
        article["Visual type"] = "No Images"
        counts["No Images"] += 1
        continue
        
    # Count photos and illustrations
    photo_count = 0
    illus_count = 0
    
    for img in images:
        # Default to 0 (photo) if the tag is somehow missing
        is_illus = img.get("Is illustration", 0)
        
        if is_illus == 1:
            illus_count += 1
        else:
            photo_count += 1
            
    # Apply your exact classification rules
    if illus_count == 0 and photo_count > 0:
        visual_type = "Photos-only"
        
    elif illus_count >= photo_count and illus_count > 0:
        # More illustrations than photos, or an equal amount (e.g. 1 and 1)
        visual_type = "Illustration-based"
        
    elif 0 < illus_count < photo_count:
        # Both exist, but there are less illustrations than photos
        visual_type = "Mixed"
        
    else:
        visual_type = "Unknown" # Failsafe
        
    # Save the label right into the article's dictionary
    article["Visual type"] = visual_type
    counts[visual_type] += 1

# 3. Save the updated dataset
print(f"Saving updated dataset to '{output_filename}'...")
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

# Print a nice summary
print("\n=== SUMMARY OF APPLIED LABELS ===")
for category, count in counts.items():
    print(f"{category:<20}: {count} articles")
print("=================================")
print("Done! You can now use this new JSON file for future analysis.")