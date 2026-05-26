import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

input_filename = 'transformed_LR_modality.json'

with open(input_filename, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

data = []

# Extract data
for article in dataset:
    emotion = article.get("primary_emotion")
    if not emotion:
        continue
        
    # Standardize text (e.g., "Fear" and "fear" become "fear")
    emotion = emotion.lower().strip()

    images = article.get("Images", [])
    article_scores = [img.get("sentiment_score") for img in images if img.get("sentiment_score") is not None]
    
    if article_scores:
        avg_img_score = sum(article_scores) / len(article_scores)
        data.append({"Primary Emotion (Text)": emotion.capitalize(), "Average Image Sentiment": avg_img_score})

# Convert to Pandas DataFrame for easy plotting
df = pd.DataFrame(data)

# Sort the emotions by their median sentiment score so the chart looks organized
ordered_emotions = df.groupby("Primary Emotion (Text)")["Average Image Sentiment"].median().sort_values().index

# Draw the Boxplot
plt.figure(figsize=(12, 6))
sns.boxplot(
    data=df, 
    x="Primary Emotion (Text)", 
    y="Average Image Sentiment", 
    order=ordered_emotions,
    palette="coolwarm" # Colors range from blue (negative) to red (positive)
)

# Formatting
plt.title("Images' sentiment and texts' primary emotions", fontsize=16, fontweight='bold')
plt.axhline(0, color='black', linestyle='--', alpha=0.5, label='Neutral Image Line')
plt.ylim(-1.1, 1.1)
plt.ylabel("Average Image Sentiment Score")
plt.xlabel("Text Primary Emotion")
plt.legend()
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.show()