import json
import os
import urllib.parse

def delete_converted_pngs():
    json_file = 'filtered_text_holod.json'
    pics_folder = 'pics'
    
    if not os.path.exists(pics_folder):
        print(f"Folder {pics_folder} does not exist")
        return
    
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
    
    # Collect all PNG URLs and derive saved filenames
    png_base_names = set()
    
    for article in articles:
        if not isinstance(article, dict) or 'Images' not in article:
            continue
        
        images = article['Images']
        if not isinstance(images, list):
            continue
        
        for url in images:
            if not isinstance(url, str):
                continue
            
            # Check if original was PNG (case insensitive)
            lower_url = url.lower()
            if lower_url.endswith('.png'):
                # Parse filename
                parsed = urllib.parse.urlparse(url)
                original_filename = os.path.basename(parsed.path)
                
                if original_filename:
                    # Create safe basename (same logic as download script)
                    safe_name = "".join(c for c in original_filename if c.isalnum() or c in '._-')
                    base_name = os.path.splitext(safe_name)[0]
                    png_base_names.add(base_name)
    
    print(f"Found {len(png_base_names)} unique PNG base names in JSON")
    
    # Find and delete corresponding JPG files in /pics
    deleted_count = 0
    not_found = []
    
    for base_name in png_base_names:
        # The download script saves as: {base_name}.jpg
        # And for duplicates: {base_name}_1.jpg, {base_name}_2.jpg, etc.
        
        # Check for base file
        jpg_name = f"{base_name}.jpg"
        jpg_path = os.path.join(pics_folder, jpg_name)
        
        if os.path.exists(jpg_path):
            os.remove(jpg_path)
            print(f"🗑️  Deleted: {jpg_name}")
            deleted_count += 1
        
        # Check for numbered variants (duplicates)
        counter = 1
        while True:
            numbered_name = f"{base_name}_{counter}.jpg"
            numbered_path = os.path.join(pics_folder, numbered_name)
            
            if os.path.exists(numbered_path):
                os.remove(numbered_path)
                print(f"🗑️  Deleted: {numbered_name}")
                deleted_count += 1
                counter += 1
            else:
                break
    
    print(f"\nComplete! Deleted {deleted_count} JPEG files originally converted from PNG")

if __name__ == "__main__":
    delete_converted_pngs()