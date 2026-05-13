import json
import os
from urllib.parse import urlparse, unquote

ARTICLES_JSON_PATH = 'filtered_text_holod_labeled.json'
SENTIMENTS_JSON_PATH = 'image_sentiment_results.json'
OUTPUT_JSON_PATH = 'filtered_text_holod_final.json'

def main():
    # 2. Load the sentiment analysis JSON
    try:
        with open(SENTIMENTS_JSON_PATH, 'r', encoding='utf-8') as f:
            sentiments_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find '{SENTIMENTS_JSON_PATH}'.")
        return

    # Create a dictionary for instant lookup by filename
    # e.g., lookup["32e1532ec3142eb_635x0.jpg"] = { ... sentiment data ... }
    sentiment_lookup = {}
    for item in sentiments_data:
        sentiment_lookup[item['filename']] = item

    # 3. Load the previously labeled articles JSON
    try:
        with open(ARTICLES_JSON_PATH, 'r', encoding='utf-8') as f:
            articles = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find '{ARTICLES_JSON_PATH}'.")
        return

    matched_count = 0
    unmatched_count = 0

    # 4. Merge the data
    for article in articles:
        images = article.get("Images",[])
        
        for img in images:
            # Parse the filename from the URL
            parsed_url = urlparse(img["url"])
            filename = unquote(os.path.basename(parsed_url.path))
            
            # Look for the exact filename in our sentiment dictionary
            sentiment_info = sentiment_lookup.get(filename)
            
            # Fallback: If URL has .webp but the sentiment file has just .jpg
            if not sentiment_info and filename.endswith('.webp'):
                sentiment_info = sentiment_lookup.get(filename.replace('.webp', ''))
                
            # If we found sentiment data for this image, add it
            if sentiment_info:
                img["sentiment"] = sentiment_info["sentiment"]
                img["sentiment_score"] = sentiment_info["sentiment_score"]
                matched_count += 1
            else:
                # If image wasn't analyzed (e.g., it was an illustration or missing)
                img["sentiment"] = None
                img["sentiment_score"] = None
                unmatched_count += 1

    # 5. Save the final combined JSON
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
        
    print(f"Done! Successfully matched sentiments for {matched_count} images.")
    print(f"Unmatched/Skipped images (likely illustrations): {unmatched_count}")
    print(f"Final data saved to: {OUTPUT_JSON_PATH}")

if __name__ == "__main__":
    main()