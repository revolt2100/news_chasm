import json

# ==========================================
# CONFIGURATION
# ==========================================
input_json_file = "final_holod_sentiment3.json" # Change this to your current file

def main():
    print(f"Loading dataset: {input_json_file}...")
    try:
        with open(input_json_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print(f"❌ File '{input_json_file}' not found.")
        return

    # Counters
    total_images = 0
    labeled_as_photo = 0        # "Is illustration": 0
    labeled_as_illustration = 0 # "Is illustration": 1
    unlabeled_images = 0        # Missing key, or value is null/invalid
    
    articles_with_unlabeled_images = 0

    # Process the data
    for article in dataset:
        images = article.get("Images", [])
        has_unlabeled_in_this_article = False
        
        for img in images:
            total_images += 1
            
            # Extract the label
            label = img.get("Is illustration")
            
            # Check what the label is
            if label == 0:
                labeled_as_photo += 1
            elif label == 1:
                labeled_as_illustration += 1
            else:
                # This catches if the key is missing entirely, is 'null', or is an empty string
                unlabeled_images += 1
                has_unlabeled_in_this_article = True
                
        if has_unlabeled_in_this_article:
            articles_with_unlabeled_images += 1

    # ==========================================
    # REPORT
    # ==========================================
    print("\n" + "="*40)
    print("          IMAGE LABEL AUDIT")
    print("="*40)
    print(f"Total Articles scanned: {len(dataset)}")
    print(f"Total Images scanned:   {total_images}")
    print("-" * 40)
    print(f"✅ Labeled as Photos (0):       {labeled_as_photo}")
    print(f"✅ Labeled as Illustrations (1): {labeled_as_illustration}")
    print(f"⚠️  UNLABELED IMAGES:            {unlabeled_images}")
    print("-" * 40)
    
    if unlabeled_images > 0:
        print(f"Those unlabeled images are spread across {articles_with_unlabeled_images} articles.")
    else:
        print("Perfect! Every single image in your dataset has a 0 or 1 label.")
    print("="*40)

if __name__ == "__main__":
    main()