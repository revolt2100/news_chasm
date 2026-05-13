import json
import os
import requests
from urllib.parse import urlparse

# --- CONFIGURATION ---
json_filename = 'filtered_text_holod_final.json'
download_folder = 'downloaded_images'

# If you want to start from a specific image URL, paste it here. 
# Example: "https://holod.media/.../image.jpg"
# Leave it empty ("") to start from the beginning.
START_FROM_URL = "https://holod.media/wp-content/webp-express/webp-images/wp-content/cache/thumb/39/8bb15bd81511a39_635x0.jpg.webp" 
# ---------------------

os.makedirs(download_folder, exist_ok=True)

with open(json_filename, 'r', encoding='utf-8') as file:
    data = json.load(file)

downloaded_count = 0
skipped_count = 0

# If START_FROM_URL is empty, we start downloading immediately.
# If it has a URL, we wait until we find it.
start_downloading = False if START_FROM_URL else True

for article_index, article in enumerate(data):
    images = article.get("Images", [])
    
    for img_index, img in enumerate(images):
        if img.get("sentiment") is None:
            img_url = img.get("url")
            
            if img_url:
                # Check if we reached the specific image to start from
                if not start_downloading:
                    if img_url == START_FROM_URL:
                        print(f"Found starting image! Resuming downloads from here...")
                        start_downloading = True
                    else:
                        continue # Skip until we find the starting URL
                
                try:
                    parsed_url = urlparse(img_url)
                    original_filename = os.path.basename(parsed_url.path)
                    
                    filename = f"article{article_index}_img{img_index}_{original_filename}"
                    filepath = os.path.join(download_folder, filename)
                    
                    # NEW: Check if file already exists so we don't download it twice
                    if os.path.exists(filepath):
                        print(f"Skipping (already exists): {filename}")
                        skipped_count += 1
                        continue

                    print(f"Downloading: {img_url}")
                    response = requests.get(img_url, stream=True)
                    response.raise_for_status() 
                    
                    with open(filepath, 'wb') as out_file:
                        for chunk in response.iter_content(chunk_size=8192):
                            out_file.write(chunk)
                            
                    downloaded_count += 1
                    
                except requests.exceptions.RequestException as e:
                    print(f"Failed to download {img_url}. Error: {e}")

print(f"\nDone! Downloaded {downloaded_count} new images. Skipped {skipped_count} existing images.")