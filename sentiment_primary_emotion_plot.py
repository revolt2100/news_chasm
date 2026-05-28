import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats  # <-- Added for ANOVA
from statsmodels.stats.multicomp import pairwise_tukeyhsd # <-- Add this to your imports at the top!

# ==========================================
# 1. LOAD AND PROCESS DATA
# ==========================================
input_filename = 'transformed_LR_modality.json'

with open(input_filename, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

data = []

for article in dataset:
    emotion = article.get("primary_emotion")
    images = article.get("Images", [])
    
    if not emotion or not images:
        continue

    emotion = emotion.lower().strip().capitalize()
    valid_scores = []
    num_photos = 0
    num_illus = 0
    
    for img in images:
        score = img.get("sentiment_score")
        if score is not None:
            valid_scores.append(score)
            
        label = img.get("Is illustration")
        if label == 0:
            num_photos += 1
        elif label == 1:
            num_illus += 1

    if not valid_scores or (num_photos == 0 and num_illus == 0):
        continue

    avg_img_score = sum(valid_scores) / len(valid_scores)
    
    # Visual Category Logic
    if num_illus == 0 and num_photos > 0:
        v_type = "Photos-Only"
    elif num_illus > 0 and num_illus < num_photos:
        v_type = "Mixed (Fewer Illus than Photos)"
    elif num_illus >= num_photos:
        v_type = "Illustration-Based"
    else:
        continue

    data.append({
        "Primary Emotion": emotion,
        "Average Image Sentiment": avg_img_score,
        "Visual Type": v_type
    })

df = pd.DataFrame(data)

df_overall = df.copy()
df_overall["Visual Type"] = "Overall"
df_combined = pd.concat([df_overall, df], ignore_index=True)

# ==========================================
# 2. PREPARE FOR PLOTTING
# ==========================================
ordered_emotions = df_overall.groupby("Primary Emotion")["Average Image Sentiment"].median().sort_values().index

plot_categories = [
    "Overall", 
    "Photos-Only", 
    "Illustration-Based", 
    "Mixed (Fewer Illus than Photos)"
]

fig, axes = plt.subplots(2, 2, figsize=(16, 12), sharey=True)
axes = axes.flatten() 

print("="*50)
print("             ANOVA STATISTICAL REPORT")
print("="*50)

# ==========================================
# 3. DRAW PLOTS AND RUN ANOVA + TUKEY
# ==========================================
for i, category in enumerate(plot_categories):
    ax = axes[i]
    subset = df_combined[df_combined["Visual Type"] == category]
    count = len(subset)
    
    anova_text = ""
    if count > 0:
        # Group the scores by Emotion
        groups = [group["Average Image Sentiment"].values for name, group in subset.groupby("Primary Emotion") if len(group) > 1]
        
        if len(groups) > 1:
            f_stat, p_val = stats.f_oneway(*groups)
            sig_stars = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
            anova_text = f"\nANOVA: F={f_stat:.2f}, p={p_val:.4f} ({sig_stars})"
            
            print(f"\n{'-'*60}")
            print(f"CATEGORY: {category.upper()}")
            print(f"ANOVA Results -> F-stat: {f_stat:.2f} | p-value: {p_val:.4f} {sig_stars}")
            
            # --- NEW: RUN TUKEY'S HSD IF ANOVA IS SIGNIFICANT ---
            if p_val < 0.05:
                print(f"Since p < 0.05, running Tukey's HSD to find exact differences...")
                
                # Tukey requires dropping any rows that might have NaN values just to be safe
                clean_subset = subset.dropna(subset=["Average Image Sentiment", "Primary Emotion"])
                
                # Run the test
                tukey = pairwise_tukeyhsd(
                    endog=clean_subset["Average Image Sentiment"], # The numerical data
                    groups=clean_subset["Primary Emotion"],        # The categories to compare
                    alpha=0.05                                     # 95% confidence interval
                )
                
                # Print the results table
                print(tukey)
                # ... [Previous Tukey Code] ...
            print(tukey)
            
            # ==========================================
            # NEW: ONE-VS-REST WELCH'S T-TEST
            # ==========================================
            print(f"\n--- ONE-VS-REST ANALYSIS ({category}) ---")
            print("Comparing each emotion against ALL other emotions combined:")
            print(f"{'Target Emotion':<15} | {'Target Mean':<12} | {'Rest Mean':<12} | {'p-value':<10} | {'Significant?'}")
            print("-" * 75)
            
            emotions = clean_subset["Primary Emotion"].unique()
            
            for target_emotion in emotions:
                # 1. Split the data into "Target" and "Everything Else"
                target_data = clean_subset[clean_subset["Primary Emotion"] == target_emotion]["Average Image Sentiment"]
                rest_data = clean_subset[clean_subset["Primary Emotion"] != target_emotion]["Average Image Sentiment"]
                
                # 2. Only run if we have enough data (at least 2 articles in both groups)
                if len(target_data) > 1 and len(rest_data) > 1:
                    
                    # 3. Run Welch's T-Test (equal_var=False makes it Welch's instead of Student's)
                    t_stat, p_val = stats.ttest_ind(target_data, rest_data, equal_var=False)
                    
                    # 4. Format the output
                    sig = "Yes (***)" if p_val < 0.001 else "Yes (**)" if p_val < 0.01 else "Yes (*)" if p_val < 0.05 else "No"
                    target_mean = target_data.mean()
                    rest_mean = rest_data.mean()
                    
                    print(f"{target_emotion:<15} | {target_mean:<12.4f} | {rest_mean:<12.4f} | {p_val:<10.4f} | {sig}")
            else:
                print("No significant difference found overall, so skipping Tukey's test.")
                
        else:
            anova_text = "\nANOVA: Insufficient variance data"
            
    # --- DRAW VIOLIN PLOT ---
    if not subset.empty:
        sns.violinplot(
            data=subset, x="Primary Emotion", y="Average Image Sentiment", 
            order=ordered_emotions, palette="coolwarm", inner="quartile", cut=0, ax=ax
        )
    
    # Formatting
    ax.set_title(f"{category} (n={count}){anova_text}", fontsize=13, fontweight='bold')
    ax.axhline(0, color='black', linestyle='--', alpha=0.6, label='Neutral (0.0)')
    ax.set_ylim(-1.1, 1.1)
    ax.set_xlabel("") 
    ax.set_ylabel("Avg Image Sentiment" if i % 2 == 0 else "") 
    ax.grid(axis='y', alpha=0.3)
    ax.tick_params(axis='x', rotation=45)

# ==========================================
# 4. FINAL TOUCHES
# ==========================================
plt.suptitle("Density of Image Sentiment Across Text Primary Emotions", fontsize=20, fontweight='bold', y=1.04)

handles, labels = axes[0].get_legend_handles_labels()
if handles:
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 1.00), fontsize=12)

plt.tight_layout()
plt.show()