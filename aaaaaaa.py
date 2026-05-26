import json

input_filename = 'final_holod_sentiment.json' # <-- Change to your 1000-article file

with open(input_filename, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# Counters
reasons = {
    "text_key_missing": 0,
    "text_score_is_null": 0,
    "no_images_array": 0,
    "empty_images_array": 0,
    "image_keys_missing_or_null": 0,
    "perfectly_fine": 0
}

print("Running Audit...\n")

# Open a text file to write the exact reasons for every dropped article
with open('debug_report.txt', 'w', encoding='utf-8') as out:
    for i, article in enumerate(dataset):
        url = article.get("URL", f"Article_Index_{i}")
        
        # 1. Check Text Score
        if "sentiment_score" not in article:
            reasons["text_key_missing"] += 1
            out.write(f"SKIPPED: {url} -> Text is missing the 'sentiment_score' key completely.\n")
            continue
            
        if article["sentiment_score"] is None:
            reasons["text_score_is_null"] += 1
            out.write(f"SKIPPED: {url} -> Text 'sentiment_score' is literally null.\n")
            continue
            
        # 2. Check Image Array
        if "Images" not in article:
            reasons["no_images_array"] += 1
            out.write(f"SKIPPED: {url} -> Article has no 'Images' key at all.\n")
            continue
            
        images = article["Images"]
        if len(images) == 0:
            reasons["empty_images_array"] += 1
            out.write(f"SKIPPED: {url} -> Article has an empty 'Images' array: [].\n")
            continue
            
        # 3. Check Image Scores
        has_valid_image = False
        for img in images:
            if "sentiment_score" in img and img["sentiment_score"] is not None:
                has_valid_image = True
                break
                
        if not has_valid_image:
            reasons["image_keys_missing_or_null"] += 1
            out.write(f"SKIPPED: {url} -> Images exist, but none of them have a 'sentiment_score'.\n")
            continue
            
        # If it passes all tests!
        reasons["perfectly_fine"] += 1

# Print the final verdict to the terminal
print("="*40)
print("             AUDIT RESULTS")
print("="*40)
print(f"Total Articles Audited:     {len(dataset)}\n")
print(f"1. Text score key missing:  {reasons['text_key_missing']}")
print(f"2. Text score is 'null':    {reasons['text_score_is_null']}")
print(f"3. 'Images' key missing:    {reasons['no_images_array']}")
print(f"4. 'Images' array is []:    {reasons['empty_images_array']}  <-- (Very common!)")
print(f"5. Image score missing:     {reasons['image_keys_missing_or_null']}")
print("-" * 40)
print(f"HEALTHY ARTICLES TO PLOT:   {reasons['perfectly_fine']}")
print("="*40)
print("\nLook at 'debug_report.txt' to see the exact URL of every skipped article and why it was skipped!")