import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# 1. Load the data
input_filename = 'classified_holod_data.json' # Or 'cleaned_holod_data.json'

with open(input_filename, 'r', encoding='utf-8') as file:
    dataset = json.load(file)

# 2. Prepare our three data categories
# Universal
x_all, y_all = [], []
# Illustrations
x_illus, y_illus = [], []
# Photos (Not illustrations)
x_photo, y_photo = [], []

for article in dataset:
    text_score = article.get("sentiment_score")
    if text_score is None:
        continue

    images = article.get("Images", [])
    
    # Temporary lists for this specific article
    all_scores = []
    illus_scores = []
    photo_scores = []
    
    for image in images:
        img_score = image.get("sentiment_score")
        if img_score is None:
            continue
            
        is_illus = image.get("Is illustration", 0) # Defaults to 0 if missing
        
        all_scores.append(img_score)
        if is_illus == 1:
            illus_scores.append(img_score)
        else:
            photo_scores.append(img_score)
            
    # Calculate averages and append to the main lists if data exists
    if all_scores:
        x_all.append(text_score)
        y_all.append(float(np.mean(all_scores)))
        
    if illus_scores:
        x_illus.append(text_score)
        y_illus.append(float(np.mean(illus_scores)))
        
    if photo_scores:
        x_photo.append(text_score)
        y_photo.append(float(np.mean(photo_scores)))

# ==========================================
# 3. HELPER FUNCTION TO DRAW EACH PLOT
# ==========================================
def draw_hex_plot(ax, x_data, y_data, title):
    # If a category is empty (e.g. no illustrations), skip drawing to prevent errors
    if not x_data:
        ax.set_title(f"{title} (No Data)")
        return None

    X = np.array(x_data).reshape(-1, 1)
    Y = np.array(y_data)
    threshold = 0.15

    # Calculate Regression Line specifically for this subset of data
    model = LinearRegression()
    model.fit(X, Y)
    slope = model.coef_[0]
    intercept = model.intercept_

    # Draw Hexbin
    hb = ax.hexbin(
        X.flatten(), Y, 
        gridsize=18, 
        cmap='Purples', 
        mincnt=1, 
        edgecolors='white', 
        linewidths=0.5
    )

    # Draw Regression lines
    line_x = np.linspace(min(X), max(X), 100).reshape(-1, 1)
    line_y = model.predict(line_x)

    ax.plot(line_x, line_y, color='orange', linewidth=2, label=f'Trend (Slope: {slope:.2f})')
    ax.plot(line_x, line_y + threshold, color='gray', linestyle='--', alpha=0.7)
    ax.plot(line_x, line_y - threshold, color='gray', linestyle='--', alpha=0.7)

    # Formatting
    ax.set_title(f"{title}\n(n={len(x_data)})", fontweight='bold')
    ax.set_xlabel('Text Sentiment Score')
    ax.set_ylabel('Image Sentiment Score')
    ax.axhline(0, color='black', linewidth=0.5, alpha=0.5) 
    ax.axvline(0, color='black', linewidth=0.5, alpha=0.5) 
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.legend(loc='lower right', fontsize=8)
    
    return hb

# ==========================================
# 4. CREATE THE FIGURE WITH 3 SUBPLOTS
# ==========================================
# figsize=(18, 6) creates a wide image with 1 row, 3 columns
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Draw the three plots
hb_all = draw_hex_plot(axes[0], x_all, y_all, "Universal (All Images)")
hb_illus = draw_hex_plot(axes[1], x_illus, y_illus, "Only Illustrations")
hb_photo = draw_hex_plot(axes[2], x_photo, y_photo, "Only Photos")

# Add a shared colorbar on the far right
# We use hb_all as the reference for the color scale
if hb_all:
    cbar = fig.colorbar(hb_all, ax=axes.ravel().tolist(), fraction=0.02, pad=0.02)
    cbar.set_label('Number of Articles')

# Add a master title
plt.suptitle('Sentiment Alignment: Text vs. Images (By Image Type)', fontsize=16, y=1.02)

# Adjust layout so nothing overlaps
plt.tight_layout()
plt.show()