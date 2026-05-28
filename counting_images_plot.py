import json
import numpy as np
import matplotlib.pyplot as plt

# 1. LOAD YOUR JSON 
input_filename = 'visual_types_added.json' 

with open(input_filename, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# 2. PREPARE DATA STRUCTURES
visual_types = ["Photos-only", "Illustration-based", "Mixed"]

stats = {
    vtype: {"photos": [], "illus": [], "total": []} for vtype in visual_types
}

# 3. PROCESS THE DATA
for article in dataset:
    vtype = article.get("Visual type")
    
    if vtype not in visual_types:
        continue
        
    images = article.get("Images", [])
    
    photo_count = 0
    illus_count = 0
    
    for img in images:
        if img.get("Is illustration", 0) == 1:
            illus_count += 1
        else:
            photo_count += 1
            
    total_count = photo_count + illus_count
    
    stats[vtype]["photos"].append(photo_count)
    stats[vtype]["illus"].append(illus_count)
    stats[vtype]["total"].append(total_count)

def safe_mean(lst):
    return np.mean(lst) if lst else 0

avg_photos = [safe_mean(stats[vt]["photos"]) for vt in visual_types]
avg_illus = [safe_mean(stats[vt]["illus"]) for vt in visual_types]
avg_total = [safe_mean(stats[vt]["total"]) for vt in visual_types]

# ==========================================
# 4. DRAW THE CHARTS
# ==========================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# --- PLOT 1: Grouped Bar Chart (Averages) ---
x_indexes = np.arange(len(visual_types))
width = 0.25

bars1 = ax1.bar(x_indexes - width, avg_photos, width, label='Avg Photos', color='#2980b9')
bars2 = ax1.bar(x_indexes, avg_illus, width, label='Avg Illustrations', color='#d35400')
bars3 = ax1.bar(x_indexes + width, avg_total, width, label='Avg Total Images', color='#7f8c8d')

for bars in [bars1, bars2, bars3]:
    for bar in bars:
        yval = bar.get_height()
        if yval > 0:
            ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.05, f"{yval:.1f}", 
                     ha='center', va='bottom', fontsize=9, fontweight='bold')

ax1.set_title("Average Image Counts per Article", fontsize=14, fontweight='bold')
ax1.set_xticks(x_indexes)
ax1.set_xticklabels(visual_types, fontsize=11)
ax1.set_ylabel("Number of Images")
ax1.legend()
ax1.grid(axis='y', linestyle='--', alpha=0.5)

# --- PLOT 2: VIOLIN PLOT (Distribution & Density) ---
boxplot_data = [stats[vt]["total"] for vt in visual_types]

if any(boxplot_data):
    # showmedians=True draws a line at the exact center of the data
    parts = ax2.violinplot(boxplot_data, showmeans=False, showmedians=True, showextrema=True)
    
    # Customizing the colors of the violins
    colors = ['#3498db', '#e67e22', '#2ecc71']
    for pc, color in zip(parts['bodies'], colors):
        pc.set_facecolor(color)
        pc.set_edgecolor('black')
        pc.set_alpha(0.7)
        
    # Formatting the median and boundary lines
    parts['cmedians'].set_color('black')
    parts['cmedians'].set_linewidth(2)
    parts['cmins'].set_color('black')
    parts['cmaxes'].set_color('black')
    parts['cbars'].set_color('black')

# Setting the x-axis ticks to match the visual types
ax2.set_xticks(np.arange(1, len(visual_types) + 1))
ax2.set_xticklabels(visual_types, fontsize=11)

ax2.set_title("Distribution of Total Images (Density & Spread)", fontsize=14, fontweight='bold')
ax2.set_ylabel("Total Number of Images")

# Force Y-axis to use whole numbers (you can't have half an image!)
y_max = max([max(lst) for lst in boxplot_data if lst] or [10])
ax2.set_yticks(np.arange(0, y_max + 2, max(1, y_max // 10)))

ax2.grid(axis='y', linestyle='--', alpha=0.5)

# Overall Formatting
plt.suptitle("Volume and Composition of Images by Visual Strategy", fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.show()