import json
import glob
import os

# 1. Define the target folder
folder_path = 'old'
search_pattern = os.path.join(folder_path, '*.json')

# Find and sort all JSON files in the "old" folder
json_files = glob.glob(search_pattern)
json_files.sort()

if not json_files:
    print(f"No JSON files found in the '{folder_path}' folder. Make sure the folder exists and contains your files.")
else:
    # Variables for Grand Totals across all files
    gt_total = 0
    gt_illus_only = 0
    gt_photos_only = 0
    gt_mixed = 0
    gt_no_images = 0

    # Print table header for individual files
    print("=" * 90)
    print(f"{'Filename':<35} | {'Total':<6} | {'Photos':<8} | {'Illus':<8} | {'Mixed':<8} | {'None':<6}")
    print("-" * 90)

    # 2. Process each file
    for file_path in json_files:
        filename = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                dataset = json.load(file)
            
            # Skip if the JSON isn't a list of articles
            if not isinstance(dataset, list):
                print(f"{filename[:34]:<35} | Skipped (Not a list of articles)")
                continue
                
            # Local counters for this specific file
            total_articles = len(dataset)
            illus_only = 0
            photos_only = 0
            mixed = 0
            no_images = 0
            
            for article in dataset:
                if not isinstance(article, dict):
                    continue
                    
                images = article.get("Images", [])
                if not images:
                    no_images += 1
                    continue
                    
                has_illustration = False
                has_photo = False
                
                for image in images:
                    is_illus = image.get("Is illustration", 0)
                    if is_illus == 1:
                        has_illustration = True
                    else:
                        has_photo = True
                        
                # Categorize the article
                if has_illustration and has_photo:
                    mixed += 1
                elif has_illustration and not has_photo:
                    illus_only += 1
                elif has_photo and not has_illustration:
                    photos_only += 1
                    
            # Print row for this file (truncating filename to 34 chars if it's too long)
            print(f"{filename[:34]:<35} | {total_articles:<6} | {photos_only:<8} | {illus_only:<8} | {mixed:<8} | {no_images:<6}")
            
            # Add this file's stats to the Grand Totals
            gt_total += total_articles
            gt_photos_only += photos_only
            gt_illus_only += illus_only
            gt_mixed += mixed
            gt_no_images += no_images

        except json.JSONDecodeError:
            print(f"{filename[:34]:<35} | Error: Invalid JSON format")
        except Exception as e:
            print(f"{filename[:34]:<35} | Error: {str(e)[:25]}")

    print("=" * 90)

    # 3. Print the Grand Total summary
    print("\n" + "=" * 45)
    print("GRAND TOTAL (ALL FILES IN 'old' FOLDER)")
    print("=" * 45)
    print(f"Total Articles Processed : {gt_total}")
    print("-" * 45)
    
    # Helper function to print with percentages
    def print_stat(label, count, total):
        percent = (count / total) * 100 if total > 0 else 0
        print(f"{label:<25}: {count:<5} ({percent:.1f}%)")

    print_stat("Photos-Only Articles", gt_photos_only, gt_total)
    print_stat("Illustration-Only", gt_illus_only, gt_total)
    print_stat("Mixed (Photos & Illus)", gt_mixed, gt_total)
    
    if gt_no_images > 0:
        print("-" * 45)
        print_stat("No Images", gt_no_images, gt_total)
        
    print("=" * 45)