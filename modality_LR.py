import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# 1. Load the updated JSON data
input_filename = 'transfromed_modality.json'
output_filename = 'transformed_LR_modality.json'

with open(input_filename, 'r', encoding='utf-8') as file:
    dataset = json.load(file)

# 2. Extract the X and Y variables
# X = article_images_overall_score
# Y = text_overall_score
x_data = []
y_data = []

# We only want to use articles that actually have both scores calculated (> 0)
for article in dataset:
    x = article.get("article_images_overall_score", 0)
    y = article.get("text_overall_score", 0)
    
    if x > 0 and y > 0:
        x_data.append(x)
        y_data.append(y)

# Reshape X for scikit-learn
X = np.array(x_data).reshape(-1, 1)
Y = np.array(y_data)

# 3. Perform Linear Regression
model = LinearRegression()
model.fit(X, Y)

# Get the equation of the line and R-squared
slope = model.coef_[0]
intercept = model.intercept_
r_squared = model.score(X, Y)  # <--- NEW: Calculate R²

print(f"Regression Line calculated: Y = {slope:.4f} * X + {intercept:.4f}")
print(f"R-squared (R²): {r_squared:.4f}") # <--- NEW: Print to terminal

# 4. Define our threshold for "Equal"
# This is the vertical distance from the line. 0.03 is a good starting point.
threshold = 0.03 

# 5. Classify every article and save to JSON
for article in dataset:
    x = article.get("article_images_overall_score", 0)
    y = article.get("text_overall_score", 0)
    
    if x > 0 and y > 0:
        # Calculate where the line is at this specific X
        expected_y = (slope * x) + intercept
        
        # Calculate the residual (how far above or below the line this dot is)
        difference = y - expected_y
        
        if difference > threshold:
            status = "images first"
        elif difference < -threshold:
            status = "text first"
        else:
            status = "equal"
            
        # Save the findings into the dictionary
        article["modality_status"] = status
        article["regression_difference"] = round(difference, 4)

# 6. Save back to a new JSON file
print(f"Saving classified dataset to {output_filename}...")
with open(output_filename, 'w', encoding='utf-8') as file:
    json.dump(dataset, file, ensure_ascii=False, indent=2)

# ==========================================
# BONUS: Plot the chart so you can visualize it!
# ==========================================
plt.figure(figsize=(8, 6))

# Plot the scatter dots
plt.scatter(X, Y, color='blue', s=20, label='Articles')

# Create points to draw the regression line
line_x = np.linspace(min(X), max(X), 100).reshape(-1, 1)
line_y = model.predict(line_x)

# Plot the regression line WITH R-Squared in the legend
plt.plot(line_x, line_y, color='red', linewidth=2, 
         label=f'Trend (Slope: {slope:.2f}, $R^2$: {r_squared:.3f})')

# Plot the "Equal" threshold bands (dashed lines)
plt.plot(line_x, line_y + threshold, color='gray', linestyle='--', label='+/- Threshold (Equal band)')
plt.plot(line_x, line_y - threshold, color='gray', linestyle='--')

plt.title('Text vs Image Status Classification', fontsize=14, fontweight='bold')
plt.xlabel('article_images_overall_score')
plt.ylabel('text_overall_score')

# Move the legend slightly if it blocks the data points
plt.legend(loc='lower right') 
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()