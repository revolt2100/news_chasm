import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. CONFIGURATION & DATA LOADING
# ==========================================
input_filename = 'visual_types_added.json'  # Replace with your actual JSON file name

with open(input_filename, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# The 10 News Values present in your JSON
metrics = [
    "negativity", "timeliness", "proximity", "superlativeness", "eliteness", 
    "impact", "novelty", "personalisation", "consonance", "aesthetic_appeal"
]

# Formatting names for the chart labels
metric_labels = [m.replace("_", " ").title() for m in metrics]

# ==========================================
# 2. DATA EXTRACTION
# ==========================================
data_records = []

for article in dataset:
    # Safely get and standardize the Visual Type
    raw_vtype = str(article.get("Visual type", "")).lower()
    
    if "photo" in raw_vtype and "illus" not in raw_vtype:
        v_type = "Photos Only"
    elif "illus" in raw_vtype and "photo" not in raw_vtype:
        v_type = "Illustrations-Based"
    elif "mixed" in raw_vtype or ("photo" in raw_vtype and "illus" in raw_vtype):
        v_type = "Mixed Visuals"
    else:
        continue  # Skip if no valid visual type

    record = {"Visual Type": v_type}

    # Extract Text News Values (Root level of article)
    for metric in metrics:
        val = article.get(metric)
        # Ensure 'null' becomes NaN for pandas math
        record[f"Text_{metric}"] = val if val is not None else np.nan

    # Extract Image News Values (Average across all images in the article)
    images = article.get("Images") or [] # Guard against null images array
    
    for metric in metrics:
        img_scores = []
        for img in images:
            # FIX: Guard against null "image_news_values" dicts
            img_nv = img.get("image_news_values") or {}
            
            # FIX: Ensure the specific metric actually contains a dictionary with a score
            if metric in img_nv and isinstance(img_nv[metric], dict):
                score = img_nv[metric].get("score")
                if score is not None:
                    img_scores.append(score)
        
        # Average the image scores for this specific article
        record[f"Image_{metric}"] = np.mean(img_scores) if img_scores else np.nan

    data_records.append(record)

# Convert to Pandas DataFrame 
df = pd.DataFrame(data_records)

if df.empty:
    print("Error: No valid articles found to plot. Check your JSON format.")
    exit()

# Calculate the grand mean for each category
agg_df = df.groupby("Visual Type").mean().reset_index()

# ==========================================
# 3. DRAWING THE DUMBBELL PLOT
# ==========================================
plot_categories = ["Photos Only", "Illustrations-Based", "Mixed Visuals"]

fig, axes = plt.subplots(1, 3, figsize=(20, 8), sharey=True)

# Styling colors
text_color = '#1f77b4'       # Blue for Text
img_color = '#ff7f0e'        # Orange for Image
gap_img_leads = '#2ca02c'    # Green line if Image > Text
gap_txt_leads = '#d62728'    # Red line if Text > Image

for i, cat in enumerate(plot_categories):
    ax = axes[i]
    
    # Get the data row for this specific visual type
    cat_data = agg_df[agg_df["Visual Type"] == cat]
    
    if cat_data.empty:
        ax.set_title(f"{cat}\n(No Data)", fontsize=14)
        continue
        
    cat_row = cat_data.iloc[0]

    # Plot each metric
    for y_idx, metric in enumerate(metrics):
        t_val = cat_row[f"Text_{metric}"]
        i_val = cat_row[f"Image_{metric}"]
        
        if pd.isna(t_val) or pd.isna(i_val):
            continue # Skip if data is missing
        
        # Color the connecting line based on which score is higher
        line_color = gap_img_leads if i_val > t_val else gap_txt_leads
        
        # Draw the connecting line
        ax.plot([t_val, i_val], [y_idx, y_idx], color=line_color, zorder=1, linewidth=4, alpha=0.5)
        
        # Draw the dots
        ax.scatter(t_val, y_idx, color=text_color, s=120, zorder=2, 
                   label='Text Score' if (i==0 and y_idx==0) else "")
        ax.scatter(i_val, y_idx, color=img_color, s=120, zorder=2, 
                   label='Image Score' if (i==0 and y_idx==0) else "")

    # Subplot Formatting
    ax.set_yticks(range(len(metrics)))
    ax.set_yticklabels(metric_labels, fontsize=13)
    ax.set_title(cat, fontsize=16, fontweight='bold')
    ax.set_xlabel("Average News Value Score (0 to 1)", fontsize=12)
    ax.set_xlim(0, 1.05)
    
    # Add light gridlines for readability
    ax.grid(axis='x', linestyle='--', alpha=0.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# ==========================================
# 4. FINAL TOUCHES
# ==========================================
from matplotlib.lines import Line2D
custom_lines = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor=text_color, markersize=12, label='Text Score'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor=img_color, markersize=12, label='Image Score'),
    Line2D([0], [0], color=gap_img_leads, lw=4, alpha=0.5, label='Image Score is Higher'),
    Line2D([0], [0], color=gap_txt_leads, lw=4, alpha=0.5, label='Text Score is Higher')
]

fig.legend(handles=custom_lines, loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=4, fontsize=13)
plt.suptitle("News Value Contributions: Text vs. Image by Article Visual Type", fontsize=22, fontweight='bold', y=1.12)

plt.tight_layout()
plt.show()