import json
import glob
import os

def main():
    # Find all JSON files in the current folder
    json_files = glob.glob('*.json')
    json_files.sort()

    if not json_files:
        print("No JSON files found in this directory.")
        return

    print("="*70)
    print("                 MASTER DATASET AUDIT")
    print("="*70)

    for file_path in json_files:
        filename = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
        except Exception as e:
            print(f"\n[{filename}] -> Error reading file: {e}")
            continue

        # Skip files that aren't lists of articles
        if not isinstance(dataset, list) or (len(dataset) > 0 and not isinstance(dataset[0], dict)):
            continue
            
        # Skip files that don't look like our main dataset
        if len(dataset) > 0 and "URL" not in dataset[0] and "filename" in dataset[0]:
            continue

        # --- Counters ---
        total_articles = len(dataset)
        articles_missing_txt_sent = 0
        
        total_images = 0
        images_missing_sent = 0
        
        total_photos = 0
        photos_missing_sent = 0
        
        total_illus = 0
        illus_missing_sent = 0
        
        total_unlabeled = 0
        unlabeled_missing_sent = 0

        # --- Processing ---
        for article in dataset:
            # Check Text Sentiment
            txt_score = article.get("sentiment_score")
            if not isinstance(txt_score, (int, float)):
                articles_missing_txt_sent += 1
                
            # Check Images
            images = article.get("Images", [])
            for img in images:
                total_images += 1
                
                # FIX: Check if 'img' is actually a dictionary!
                if isinstance(img, dict):
                    img_score = img.get("sentiment_score")
                    has_score = isinstance(img_score, (int, float))
                    label = img.get("Is illustration")
                else:
                    # It's a string (raw URL) or something else. It definitely has no score/label.
                    has_score = False
                    label = None
                
                if not has_score:
                    images_missing_sent += 1
                
                # Count Labels
                if label == 0:
                    total_photos += 1
                    if not has_score:
                        photos_missing_sent += 1
                elif label == 1:
                    total_illus += 1
                    if not has_score:
                        illus_missing_sent += 1
                else:
                    total_unlabeled += 1
                    if not has_score:
                        unlabeled_missing_sent += 1

        # --- Print Report for this File ---
        print(f"\n📂 FILE: {filename}")
        print("-" * 70)
        print(f"📄 ARTICLES:      {total_articles:<5} (Missing Text Sentiment: {articles_missing_txt_sent})")
        print(f"🖼️  TOTAL IMAGES:  {total_images:<5} (Missing Img Sentiment: {images_missing_sent})")
        print("   Breakdown by label:")
        print(f"   - Photos (0):        {total_photos:<5} (Missing Sent: {photos_missing_sent})")
        print(f"   - Illustrations (1): {total_illus:<5} (Missing Sent: {illus_missing_sent})")
        if total_unlabeled > 0:
            print(f"   - Unlabeled:         {total_unlabeled:<5} (Missing Sent: {unlabeled_missing_sent})")
        print("-" * 70)

if __name__ == "__main__":
    main()