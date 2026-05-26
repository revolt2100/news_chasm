
import json
import sys

def filter_articles(input_file='holod_society_articles.json', output_file='filtered_holod.json'):
    """
    Filter news articles by removing specific image patterns and empty articles.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file (default: filtered_holod.json)
    """
    # Load input JSON
    with open('holod_society_articles.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list of articles and dict with articles key
    if isinstance(data, list):
        articles = data
        is_list = True
    elif isinstance(data, dict) and 'articles' in data:
        articles = data['articles']
        is_list = False
    else:
        # Assume single article or dict of articles
        articles = [data] if not isinstance(data, dict) or 'Images' in data else list(data.values())
        is_list = isinstance(data, list)
    
    filtered_articles = []
    removed_count = 0
    
    # Substrings to filter out
    forbidden_patterns = [
        "-208x145",
        "/autoshere-n/generated_image",
        "/assets/img/"
    ]
    
    for article in articles:
        if not isinstance(article, dict):
            continue
            
        # Check if article has Images key
        if 'Images' not in article:
            filtered_articles.append(article)
            continue
        
        images = article['Images']
        
        # Handle if Images is a list
        if isinstance(images, list):
            filtered_images = [
                img for img in images 
                if not any(pattern in str(img) for pattern in forbidden_patterns)
            ]
            
            # Only keep article if Images not empty after filtering
            if filtered_images:
                article['Images'] = filtered_images
                filtered_articles.append(article)
            else:
                removed_count += 1
                
        # Handle if Images is a set (convert to list for JSON serialization)
        elif isinstance(images, set):
            filtered_images = {
                img for img in images 
                if not any(pattern in str(img) for pattern in forbidden_patterns)
            }
            
            if filtered_images:
                article['Images'] = list(filtered_images)  # Convert set to list for JSON
                filtered_articles.append(article)
            else:
                removed_count += 1
        else:
            # If Images is neither list nor set, keep as is
            filtered_articles.append(article)
    
    # Prepare output data maintaining original structure
    if is_list:
        output_data = filtered_articles
    else:
        output_data = {**data, 'articles': filtered_articles}
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"Processing complete:")
    print(f"  Original articles: {len(articles)}")
    print(f"  Removed articles: {removed_count}")
    print(f"  Remaining articles: {len(filtered_articles)}")
    print(f"  Output saved to: {output_file}")

if __name__ == "__main__":
    filter_articles()