import json
import os
import requests
from PIL import Image
from io import BytesIO
import urllib.parse
from tqdm import tqdm

def download_and_convert_images():
    json_file = 'filtered_text_holod.json'
    output_folder = 'pics'
    
    # Ensure folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
    
    # Load JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, list):
        articles = data
    elif isinstance(data, dict) and 'articles' in data:
        articles = data['articles']
    else:
        articles = [data] if isinstance(data, dict) else []
    
    # Collect all image URLs first
    urls = []
    for article in articles:
        if not isinstance(article, dict) or 'Images' not in article:
            continue
        images = article['Images']
        if isinstance(images, list):
            for url in images:
                if isinstance(url, str) and url.lower().endswith(valid_extensions):
                    urls.append(url)
    
    print(f"Found {len(urls)} images")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    downloaded = 0
    skipped = 0
    errors = 0
    
    # Process with progress bar
    for img_url in tqdm(urls, desc="Downloading", unit="img"):
        try:
            # Parse filename from URL
            parsed = urllib.parse.urlparse(img_url)
            original_filename = os.path.basename(parsed.path)
            
            if not original_filename:
                continue
            
            # Create safe filename with .jpg extension
            safe_name = "".join(c for c in original_filename if c.isalnum() or c in '._-')
            base_name = os.path.splitext(safe_name)[0]
            output_filename = f"{base_name}.jpg"
            output_path = os.path.join(output_folder, output_filename)
            
            # Handle duplicates by checking existing files
            counter = 1
            original_path = output_path
            while os.path.exists(output_path):
                # If file exists, skip (resume capability)
                if counter == 1:
                    skipped += 1
                    tqdm.write(f"⏭ Skip (exists): {output_filename}")
                    break
                output_filename = f"{base_name}_{counter}.jpg"
                output_path = os.path.join(output_folder, output_filename)
                counter += 1
            
            if os.path.exists(original_path):
                continue
                
            # Download image
            response = requests.get(img_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Open and convert to RGB if necessary
            img = Image.open(BytesIO(response.content))
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as JPEG
            img.save(output_path, 'JPEG', quality=90)
            downloaded += 1
            tqdm.write(f"✓ Saved: {output_filename}")
            
        except requests.exceptions.RequestException as e:
            errors += 1
            tqdm.write(f"✗ Network error: {str(e)[:50]}")
        except Exception as e:
            errors += 1
            tqdm.write(f"✗ Error: {str(e)[:50]}")
    
    print(f"\nComplete! Downloaded: {downloaded}, Skipped: {skipped}, Errors: {errors}")

if __name__ == "__main__":
    download_and_convert_images()