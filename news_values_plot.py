import json
import numpy as np
import matplotlib.pyplot as plt

input_filename = 'transformed_LR_modality.json' # Change to your filename

with open(input_filename, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

nv_keys = [
    "negativity", "timeliness", "proximity", "superlativeness", 
    "eliteness", "impact", "novelty", "personalisation", 
    "consonance", "aesthetic_appeal"
]

article_types = ["Photos Only", "Illustrations based", "Mixed"]

# Data structure to hold all our numbers
data = {
    atype: {
        "text_overall": [], 
        "image_overall": [], 
        "text_nv": {k: [] for k in nv_keys}, 
        "image_nv": {k: [] for k in nv_keys},
        "combined_overall_nv": {k: [] for k in nv_keys} # NEW: Combined Text+Image score per value
    } for atype in article_types
}

# 1. PROCESS DATA
for article in dataset:
    images = article.get("Images", [])
    if not images:
        continue
        
    # Determine Article Type
    photo_count = sum(1 for img in images if img.get("Is illustration", 0) == 0)
    illus_count = sum(1 for img in images if img.get("Is illustration", 0) == 1)
    
    if illus_count == 0 and photo_count > 0:
        atype = "Photos Only"
    elif illus_count >= photo_count and illus_count > 0:
        atype = "Illustrations based"
    elif 0 < illus_count < photo_count:
        atype = "Mixed"
    else:
        continue

    # Extract Text News Values
    article_text_vals = {}
    for key in nv_keys:
        val = article.get(key)
        if isinstance(val, (int, float)):
            article_text_vals[key] = val
            data[atype]["text_nv"][key].append(val)
            
    if article_text_vals:
        data[atype]["text_overall"].append(np.mean(list(article_text_vals.values())))

    # Extract Image News Values
    img_scores_for_overall = []
    img_nv_temp = {key: [] for key in nv_keys}
    
    for img in images:
        nv_dict = img.get("image_news_values") or {}
        for key in nv_keys:
            nv_data = nv_dict.get(key) or {}
            score = nv_data.get("score") if isinstance(nv_data, dict) else None
            if isinstance(score, (int, float)):
                img_nv_temp[key].append(score)
                img_scores_for_overall.append(score)
                
    article_img_vals = {}
    if img_scores_for_overall:
        data[atype]["image_overall"].append(np.mean(img_scores_for_overall))
        for key in nv_keys:
            if img_nv_temp[key]:
                mean_img_score = np.mean(img_nv_temp[key])
                article_img_vals[key] = mean_img_score
                data[atype]["image_nv"][key].append(mean_img_score)

    # Calculate COMBINED News Values (Average of Text + Image for each specific value)
    for key in nv_keys:
        combined = []
        if key in article_text_vals:
            combined.append(article_text_vals[key])
        if key in article_img_vals:
            combined.append(article_img_vals[key])
            
        if combined:
            data[atype]["combined_overall_nv"][key].append(np.mean(combined))

# Helper to safely calculate means
def safe_mean(lst):
    return np.mean(lst) if lst else 0

# ==========================================
# 2. DRAW THE CHARTS (Separately)
# ==========================================
colors = ['#2980b9', '#d35400', '#27ae60'] # Blue, Orange, Green
nice_labels = [k.replace('_', ' ').title() for k in nv_keys]
x_idx_10 = np.arange(len(nv_keys))
width_3 = 0.25

# --- PLOT 1: Overall General Newsworthiness ---
plt.figure(figsize=(10, 6))
x_idx_3 = np.arange(len(article_types))
width_2 = 0.35

text_overalls = [safe_mean(data[at]["text_overall"]) for at in article_types]
image_overalls = [safe_mean(data[at]["image_overall"]) for at in article_types]

bars_t = plt.bar(x_idx_3 - width_2/2, text_overalls, width_2, label='Text Overall', color='#34495e')
bars_i = plt.bar(x_idx_3 + width_2/2, image_overalls, width_2, label='Images Overall', color='#e74c3c')

for bars in [bars_t, bars_i]:
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.01, f"{yval:.2f}", ha='center', va='bottom', fontweight='bold')

plt.title("General Newsworthiness: Text vs Images (By Article Type)", fontsize=14, fontweight='bold')
plt.xticks(x_idx_3, article_types, fontsize=12)
plt.ylabel("Average Score (0 to 1)")
plt.ylim(0, 1.1)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()

# --- PLOT 2: Image Metrics Only ---
plt.figure(figsize=(14, 6))
for i, atype in enumerate(article_types):
    vals = [safe_mean(data[atype]["image_nv"][k]) for k in nv_keys]
    offset = (i - 1) * width_3
    plt.bar(x_idx_10 + offset, vals, width_3, label=atype, color=colors[i])

plt.title("Image Metrics: Specific News Values in the Visuals", fontsize=14, fontweight='bold')
plt.xticks(x_idx_10, nice_labels, rotation=30, ha='right')
plt.ylabel("Average Score (0 to 1)")
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()

# --- PLOT 3: Text Metrics Only ---
plt.figure(figsize=(14, 6))
for i, atype in enumerate(article_types):
    vals = [safe_mean(data[atype]["text_nv"][k]) for k in nv_keys]
    offset = (i - 1) * width_3
    plt.bar(x_idx_10 + offset, vals, width_3, label=atype, color=colors[i])

plt.title("Text Metrics: Specific News Values in the Written Story", fontsize=14, fontweight='bold')
plt.xticks(x_idx_10, nice_labels, rotation=30, ha='right')
plt.ylabel("Average Score (0 to 1)")
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()

# --- PLOT 4: Combined Overall News Values (Text + Image Averaged) ---
plt.figure(figsize=(14, 6))
for i, atype in enumerate(article_types):
    vals = [safe_mean(data[atype]["combined_overall_nv"][k]) for k in nv_keys]
    offset = (i - 1) * width_3
    plt.bar(x_idx_10 + offset, vals, width_3, label=atype, color=colors[i])

plt.title("Overall Combined Metrics (Text + Image Averages)", fontsize=14, fontweight='bold')
plt.xticks(x_idx_10, nice_labels, rotation=30, ha='right')
plt.ylabel("Average Combined Score (0 to 1)")
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()

# Show all 4 plots at once (They will open in separate windows)
plt.show()