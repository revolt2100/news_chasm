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

# Data structure
data = {
    atype: {
        "text_nv": {k: [] for k in nv_keys}, 
        "image_nv": {k: [] for k in nv_keys}
    } for atype in article_types
}

# 1. PROCESS DATA
for article in dataset:
    images = article.get("Images", [])
    if not images:
        continue
        
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
    for key in nv_keys:
        val = article.get(key)
        if isinstance(val, (int, float)):
            data[atype]["text_nv"][key].append(val)

    # Extract Image News Values
    img_nv_temp = {key: [] for key in nv_keys}
    for img in images:
        nv_dict = img.get("image_news_values") or {}
        for key in nv_keys:
            nv_data = nv_dict.get(key) or {}
            score = nv_data.get("score") if isinstance(nv_data, dict) else None
            if isinstance(score, (int, float)):
                img_nv_temp[key].append(score)
                
    for key in nv_keys:
        if img_nv_temp[key]:
            data[atype]["image_nv"][key].append(np.mean(img_nv_temp[key]))

def safe_mean(lst):
    return np.mean(lst) if lst else 0

# ==========================================
# 2. DRAW THE CHARTS
# ==========================================
nice_labels = [k.replace('_', ' ').title() for k in nv_keys]
x_idx = np.arange(len(nv_keys))
width = 0.35

color_text = '#34495e' # Dark Slate
color_img = '#e74c3c'  # Vibrant Red

# Helper function to draw the side-by-side comparison plots
def draw_comparison_plot(atype, fignum):
    plt.figure(fignum, figsize=(12, 6))
    
    text_vals = [safe_mean(data[atype]["text_nv"][k]) for k in nv_keys]
    img_vals = [safe_mean(data[atype]["image_nv"][k]) for k in nv_keys]
    
    bars_t = plt.bar(x_idx - width/2, text_vals, width, label='Text Contribution', color=color_text)
    bars_i = plt.bar(x_idx + width/2, img_vals, width, label='Image Contribution', color=color_img)
    
    plt.title(f"Who Contributes More? Text vs Image in '{atype}' Articles", fontsize=14, fontweight='bold')
    plt.xticks(x_idx, nice_labels, rotation=30, ha='right')
    plt.ylabel("Average Score (0 to 1)")
    plt.ylim(0, 1.1)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()

# Draw Plots 1, 2, and 3
draw_comparison_plot("Photos Only", 1)
draw_comparison_plot("Illustrations based", 2)
draw_comparison_plot("Mixed", 3)


# --- PLOT 4: The "Contribution Gap" (Image Score minus Text Score) ---
# This shows the DELTA. Above 0 = Image dominates. Below 0 = Text dominates.
plt.figure(4, figsize=(14, 6))
width_gap = 0.25
colors_gap = ['#2980b9', '#d35400', '#27ae60'] # Blue, Orange, Green

for i, atype in enumerate(article_types):
    gap_vals = []
    for k in nv_keys:
        t_mean = safe_mean(data[atype]["text_nv"][k])
        i_mean = safe_mean(data[atype]["image_nv"][k])
        # Calculate the gap (Image minus Text)
        gap_vals.append(i_mean - t_mean)
        
    offset = (i - 1) * width_gap
    plt.bar(x_idx + offset, gap_vals, width_gap, label=atype, color=colors_gap[i])

plt.title("The Contribution Gap: Image Score minus Text Score", fontsize=15, fontweight='bold')
plt.xticks(x_idx, nice_labels, rotation=30, ha='right')
plt.ylabel("Gap Difference\n(< 0 Text Leads | > 0 Image Leads)")

# Draw a thick zero line so it's easy to see who wins
plt.axhline(0, color='black', linewidth=1.5)

plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()

# Show all 4 plots at once
plt.show()