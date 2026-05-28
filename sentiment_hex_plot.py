import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# 1. LOAD YOUR JSON
input_filename = 'transformed_LR_modality.json' # Change to your final filename

with open(input_filename, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# Arrays for Top Row
x_article_avg, y_article_avg = [], []
x_illus_single, y_illus_single = [], []
x_photo_single, y_photo_single = [], []

# Arrays for Bottom Row (The 3 New Categories)
x_photos_only, y_photos_only = [], []
x_illus_based, y_illus_based = [], []
x_mixed, y_mixed = [], []

# 2. PROCESS DATA
for article in dataset:
    raw_text_score = article.get("sentiment_score")
    if raw_text_score is None:
        continue
        
    try:
        text_score = float(raw_text_score)
    except (ValueError, TypeError):
        continue

    images = article.get("Images", [])
    if not images:
        continue 

    article_all_image_scores = []
    photo_count = 0
    illus_count = 0

    for img in images:
        raw_img_score = img.get("sentiment_score")
        if raw_img_score is None:
            continue
            
        try:
            img_score = float(raw_img_score)
            article_all_image_scores.append(img_score)
            
            # Check if illustration or photo
            is_illus = img.get("Is illustration", 0)
            
            if is_illus == 1:
                illus_count += 1
                x_illus_single.append(text_score)
                y_illus_single.append(img_score)
            else:
                photo_count += 1
                x_photo_single.append(text_score)
                y_photo_single.append(img_score)
                
        except (ValueError, TypeError):
            continue
            
    # Calculate Article-level average and categorize
    if article_all_image_scores:
        article_avg = float(np.mean(article_all_image_scores))
        
        # Add to the Universal Article Average plot
        x_article_avg.append(text_score)
        y_article_avg.append(article_avg)
        
        # Sort into the 3 new categories
        if illus_count == 0 and photo_count > 0:
            x_photos_only.append(text_score)
            y_photos_only.append(article_avg)
        elif illus_count >= photo_count and illus_count > 0:
            x_illus_based.append(text_score)
            y_illus_based.append(article_avg)
        elif 0 < illus_count < photo_count:
            x_mixed.append(text_score)
            y_mixed.append(article_avg)

# ==========================================
# 3. HELPER FUNCTION TO DRAW EACH PLOT
# ==========================================
def draw_hex_plot(ax, x_data, y_data, title, y_label):
    if not x_data:
        ax.set_title(f"{title}\n(No Data)")
        return None

    X = np.array(x_data).reshape(-1, 1)
    Y = np.array(y_data)
    threshold = 0.15

    model = LinearRegression()
    model.fit(X, Y)
    
    # --- NEW: CALCULATE R-SQUARED ---
    slope = model.coef_[0]
    r_squared = model.score(X, Y)

    hb = ax.hexbin(
        X.flatten(), Y, 
        gridsize=15, cmap='Purples', mincnt=1, 
        edgecolors='white', linewidths=0.5
    )

    line_x = np.linspace(-1.1, 1.1, 100).reshape(-1, 1)
    line_y = model.predict(line_x)

    # --- NEW: ADD R² TO THE LEGEND LABEL ---
    ax.plot(line_x, line_y, color='orange', linewidth=2, 
            label=f'Trend (Slope: {slope:.2f}, $R^2$: {r_squared:.3f})')
            
    ax.plot(line_x, line_y + threshold, color='gray', linestyle='--', alpha=0.7)
    ax.plot(line_x, line_y - threshold, color='gray', linestyle='--', alpha=0.7)

    ax.set_title(f"{title}\n(n={len(x_data)})", fontweight='bold')
    ax.set_xlabel('Text Sentiment (-1 to 1)')
    ax.set_ylabel(y_label)
    ax.axhline(0, color='black', linewidth=0.5, alpha=0.5) 
    ax.axvline(0, color='black', linewidth=0.5, alpha=0.5) 
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    
    # Adjusted legend size slightly to fit the new text
    ax.legend(loc='lower right', fontsize=9)
    
    return hb

# ==========================================
# 4. CREATE THE FIGURE (2 Rows, 3 Columns)
# ==========================================
fig, axes = plt.subplots(2, 3, figsize=(18, 12)) 

# --- Top Row ---
hb_all = draw_hex_plot(axes[0, 0], x_article_avg, y_article_avg, "Article-Level: All Images", "Average Image Sentiment")
draw_hex_plot(axes[0, 1], x_illus_single, y_illus_single, "Image-Level: Individual Illustrations", "Single Illustration Sentiment")
draw_hex_plot(axes[0, 2], x_photo_single, y_photo_single, "Image-Level: Individual Photos", "Single Photo Sentiment")

# --- Bottom Row ---
draw_hex_plot(axes[1, 0], x_photos_only, y_photos_only, "Article-Level: 'Photos Only'", "Average Image Sentiment")
draw_hex_plot(axes[1, 1], x_illus_based, y_illus_based, "Article-Level: 'Illustrations Based'", "Average Image Sentiment")
draw_hex_plot(axes[1, 2], x_mixed, y_mixed, "Article-Level: 'Mixed'", "Average Image Sentiment")

# Add a shared colorbar on the far right
if hb_all:
    cbar = fig.colorbar(hb_all, ax=axes.ravel().tolist(), fraction=0.015, pad=0.02)
    cbar.set_label('Density (Number of Data Points)')

plt.suptitle('Sentiment Alignment: By Visual Composition (Holod Media)', fontsize=20, y=0.98, fontweight='bold')
plt.show()