import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# 1. LOAD YOUR JSON
input_filename = 'AGAINholod_enriched3.json' # Change to your final filename

with open(input_filename, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# Arrays for Plot 1: Article-Level Averages (All Images)
x_article_avg, y_article_avg = [], []

# Arrays for Plot 2 & 3: Individual Single Images
x_illus_single, y_illus_single = [], []
x_photo_single, y_photo_single = [], []

# 2. PROCESS DATA
for article in dataset:
    # --- Check Text Score ---
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

    # Track scores to calculate the article average later
    article_all_image_scores = []

    for img in images:
        raw_img_score = img.get("sentiment_score")
        if raw_img_score is None:
            continue
            
        try:
            img_score = float(raw_img_score)
            
            # 1. Add to the list for the article average
            article_all_image_scores.append(img_score)
            
            # 2. Assign to Individual Image Plots based on the label!
            is_illus = img.get("Is illustration", 0)
            
            if is_illus == 1:
                x_illus_single.append(text_score)
                y_illus_single.append(img_score)
            else:
                x_photo_single.append(text_score)
                y_photo_single.append(img_score)
                
        except (ValueError, TypeError):
            continue
            
    # 3. Calculate the article's overall average for Plot 1
    if article_all_image_scores:
        x_article_avg.append(text_score)
        y_article_avg.append(float(np.mean(article_all_image_scores)))

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
    slope = model.coef_[0]

    # Draw the hex map
    hb = ax.hexbin(
        X.flatten(), Y, 
        gridsize=15, 
        cmap='Purples', 
        mincnt=1, 
        edgecolors='white', 
        linewidths=0.5
    )

    line_x = np.linspace(-1.1, 1.1, 100).reshape(-1, 1)
    line_y = model.predict(line_x)

    # Draw Trend lines
    ax.plot(line_x, line_y, color='orange', linewidth=2, label=f'Trend (Slope: {slope:.2f})')
    ax.plot(line_x, line_y + threshold, color='gray', linestyle='--', alpha=0.7)
    ax.plot(line_x, line_y - threshold, color='gray', linestyle='--', alpha=0.7)

    # Formatting
    # Notice we now say 'n=' to show exactly how many dots/hexes are in the plot
    ax.set_title(f"{title}\n(n={len(x_data)})", fontweight='bold')
    ax.set_xlabel('Text Sentiment Score (-1 to 1)')
    ax.set_ylabel(y_label)
    
    # Crosshairs
    ax.axhline(0, color='black', linewidth=0.5, alpha=0.5) 
    ax.axvline(0, color='black', linewidth=0.5, alpha=0.5) 
    
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.legend(loc='lower right', fontsize=8)
    
    return hb

# ==========================================
# 4. CREATE THE FIGURE
# ==========================================
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Plot 1: Article Level
hb_all = draw_hex_plot(
    axes[0], x_article_avg, y_article_avg, 
    "Article-Level: All Images", 
    "Average Image Sentiment"
)

# Plot 2: Image Level (Illustrations)
hb_illus = draw_hex_plot(
    axes[1], x_illus_single, y_illus_single, 
    "Image-Level: Individual Illustrations", 
    "Single Illustration Sentiment"
)

# Plot 3: Image Level (Photos)
hb_photo = draw_hex_plot(
    axes[2], x_photo_single, y_photo_single, 
    "Image-Level: Individual Photos", 
    "Single Photo Sentiment"
)

# Add a shared colorbar on the far right
if hb_all:
    cbar = fig.colorbar(hb_all, ax=axes.ravel().tolist(), fraction=0.02, pad=0.02)
    cbar.set_label('Density (Number of Data Points)')

plt.suptitle('Sentiment Alignment: Text vs. Images (Holod Media)', fontsize=16, y=1.02)
plt.show()