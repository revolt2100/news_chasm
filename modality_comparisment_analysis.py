import json
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. CONFIGURATION
# ==========================================
input_json_file = "transformed_LR_modality.json" # Change to your JSON filename

with open(input_json_file, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# Initialize counters with the new category names
data_counts = {
    "Photos Only": {"text first": 0, "images first": 0, "equal": 0},
    "Illustrations based": {"text first": 0, "images first": 0, "equal": 0},
    "Mixed": {"text first": 0, "images first": 0, "equal": 0}
}

# ==========================================
# 2. PROCESS DATA
# ==========================================
for article in dataset:
    modality = article.get("modality_status")
    images = article.get("Images", [])
    
    # Skip articles that are missing a modality status or have no images
    if not modality or not images:
        continue
        
    # Standardize the modality string just in case
    modality = modality.lower().strip()
    if modality not in ["text first", "images first", "equal"]:
        continue
        
    # Replace boolean flags with exact counters
    photo_count = 0
    illus_count = 0
    
    for img in images:
        label = img.get("Is illustration")
        if label == 0:
            photo_count += 1
        elif label == 1:
            illus_count += 1
            
    # Categorize the article based on the new logic
    if illus_count == 0 and photo_count > 0:
        data_counts["Photos Only"][modality] += 1
    elif illus_count >= photo_count and illus_count > 0:
        data_counts["Illustrations based"][modality] += 1
    elif 0 < illus_count < photo_count:
        data_counts["Mixed"][modality] += 1

# ==========================================
# 3. PREPARE DATA FOR PLOTTING
# ==========================================
categories = list(data_counts.keys())
statuses = ["text first", "equal", "images first"]
colors = ['#1f77b4', '#7f7f7f', '#ff7f0e'] # Blue (Text), Grey (Equal), Orange (Images)

# Extract raw numbers
raw_data = {status: [data_counts[cat][status] for cat in categories] for status in statuses}

# Calculate percentages for the 100% stacked bar chart
pct_data = {status: [] for status in statuses}
for i, cat in enumerate(categories):
    total = sum(data_counts[cat][s] for s in statuses)
    for status in statuses:
        # Avoid division by zero if a category is completely empty
        pct = (raw_data[status][i] / total * 100) if total > 0 else 0
        pct_data[status].append(pct)

# ==========================================
# 4. DRAW THE CHARTS
# ==========================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

x_indexes = np.arange(len(categories))
bar_width = 0.6

# --- PLOT 1: RAW COUNTS (Stacked Bar) ---
bottom_y = np.zeros(len(categories))
for status, color in zip(statuses, colors):
    values = raw_data[status]
    bars = ax1.bar(categories, values, bottom=bottom_y, label=status.title(), color=color, width=bar_width)
    bottom_y += values
    
    # Add numbers inside the bars
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_y() + h/2, 
                     f'{int(h)}', ha='center', va='center', color='white', fontweight='bold')

ax1.set_title('Raw Article Counts by Visual Type', fontsize=14)
ax1.set_ylabel('Number of Articles')
ax1.grid(axis='y', linestyle='--', alpha=0.5)

# --- PLOT 2: PERCENTAGES (100% Stacked Bar) ---
bottom_y = np.zeros(len(categories))
for status, color in zip(statuses, colors):
    values = pct_data[status]
    bars = ax2.bar(categories, values, bottom=bottom_y, label=status.title(), color=color, width=bar_width)
    bottom_y += values
    
    # Add percentages inside the bars
    for bar in bars:
        h = bar.get_height()
        if h > 5: # Only show text if the bar is tall enough to fit it
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_y() + h/2, 
                     f'{h:.1f}%', ha='center', va='center', color='white', fontweight='bold')

ax2.set_title('Proportional Breakdown (100% Stacked)', fontsize=14)
ax2.set_ylabel('Percentage (%)')
ax2.set_ylim(0, 100)
ax2.grid(axis='y', linestyle='--', alpha=0.5)

# --- OVERALL FORMATTING ---
for ax in (ax1, ax2):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# Put one shared legend at the very top
handles, labels = ax1.get_legend_handles_labels()
fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=3, fontsize=12)

plt.suptitle("Modality Status: Photos vs. Illustrations", fontsize=18, y=1.12, fontweight='bold')
plt.tight_layout()
plt.show()