import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from huggingface_hub import login

# 1. Login to Hugging Face
login(token="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")

# 2. Load the Multilingual Model
print("Loading model...")
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')

input_filename = 'holod_images_values_concepts.json'
output_filename = 'updated_holod_data.json'

print(f"Loading data from {input_filename}...")
with open(input_filename, 'r', encoding='utf-8') as file:
    dataset = json.load(file)

# 3. Process the dataset
for article_index, article in enumerate(dataset):
    print(f"Processing Article {article_index + 1}/{len(dataset)}: {article.get('Title', 'No Title')}")

    # --- A. EXTRACT TEXT ITEMS ---
    text_items = []
    
    for entity in article.get('entities', []):
        if 'name' in entity:
            text_items.append(entity['name'])

    for concept in article.get('concepts', []):
        if 'concept' in concept:
            text_items.append(concept['concept'])

    if not text_items or not article.get('Images'):
        continue

    text_embeddings = model.encode(text_items)

    # Variables to track data for the whole article
    article_image_scores = []
    all_image_items_in_article = [] # Needed later for the text's perspective

    # --- B. PROCESS EVERY IMAGE ---
    for image_index, image in enumerate(article['Images']):
        image_items = []
        
        for obj in image.get('image_objects', []):
            if 'name' in obj:
                image_items.append(obj['name'])

        for concept in image.get('image_concepts_list', []):
            if 'name' in concept:
                image_items.append(concept['name'])

        if not image_items:
            continue
            
        all_image_items_in_article.extend(image_items)

        image_embeddings = model.encode(image_items)
        similarity_matrix = cosine_similarity(image_embeddings, text_embeddings)

        image_similarities = []
        image_scores_list = []

        # Find best text match for each image tag
        for i, img_item in enumerate(image_items):
            best_match_idx = np.argmax(similarity_matrix[i])
            best_score = float(similarity_matrix[i][best_match_idx])
            best_text_item = text_items[best_match_idx]
            
            image_similarities.append({
                "image_tag": img_item,
                "closest_text_concept": best_text_item,
                "similarity_score": round(best_score, 4)
            })
            image_scores_list.append(best_score)
            
        # 1. Save INDIVIDUAL IMAGE SCORE (Average of its tags)
        img_overall_score = float(np.mean(image_scores_list)) if image_scores_list else 0.0
        image["image_overall_score"] = round(img_overall_score, 4)
        image["text_similarities"] = image_similarities
        
        article_image_scores.append(img_overall_score)

    # --- C. CALCULATE ARTICLE-LEVEL & TEXT-LEVEL SCORES ---
    
    # 2. Save ARTICLE IMAGES SCORE (Average of all individual image scores)
    if article_image_scores:
        article["article_images_overall_score"] = round(float(np.mean(article_image_scores)), 4)
    else:
        article["article_images_overall_score"] = 0.0

    # 3. Save TEXT'S OVERALL SCORE (How well do text tags match the images?)
    if all_image_items_in_article:
        # Compare text to ALL images in the article combined
        all_images_embeddings = model.encode(all_image_items_in_article)
        text_to_images_matrix = cosine_similarity(text_embeddings, all_images_embeddings)
        
        text_similarities = []
        text_scores_list = []
        
        for i, txt_item in enumerate(text_items):
            best_match_idx = np.argmax(text_to_images_matrix[i])
            best_score = float(text_to_images_matrix[i][best_match_idx])
            best_img_item = all_image_items_in_article[best_match_idx]
            
            text_similarities.append({
                "text_concept": txt_item,
                "closest_image_tag": best_img_item,
                "similarity_score": round(best_score, 4)
            })
            text_scores_list.append(best_score)
            
        # Save Text overall score and the mappings
        text_overall_score = float(np.mean(text_scores_list)) if text_scores_list else 0.0
        article["text_overall_score"] = round(text_overall_score, 4)
        
        # (Optional but helpful) saving the specific text->image matches at the article level
        article["image_similarities_for_text"] = text_similarities


# 4. Save the updated dataset back to a new JSON file
print(f"\nSaving updated dataset to {output_filename}...")
with open(output_filename, 'w', encoding='utf-8') as file:
    json.dump(dataset, file, ensure_ascii=False, indent=2)

print("Done!")