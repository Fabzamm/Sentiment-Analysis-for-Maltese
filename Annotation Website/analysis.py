import json

# Load the JSON data
with open('combined_data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Initialize counters
total_comments = len(data)
annotation_counts = {0: 0, 1: 0, 2: 0, 3: 0, 'more': []}

# Analyze each comment
for comment in data:
    # Calculate total annotations by summing the sentiment counts
    total_annotations = comment['positive'] + comment['negative'] + comment['neutral'] + comment['ma nafx']
    
    # Categorize based on annotation count
    if total_annotations <= 3:
        annotation_counts[total_annotations] += 1
    else:
        annotation_counts['more'].append(comment['id'])

# Calculate percentages
percentages = {}
for count in [0, 1, 2, 3]:
    if total_comments > 0:
        percentages[count] = (annotation_counts[count] / total_comments) * 100
    else:
        percentages[count] = 0

# Print the results
print(f"Total comments: {total_comments}")
print(f"Total with 0 annotations: {annotation_counts[0]} ({percentages[0]:.2f}%)")
print(f"Total with 1 annotations: {annotation_counts[1]} ({percentages[1]:.2f}%)")
print(f"Total with 2 annotations: {annotation_counts[2]} ({percentages[2]:.2f}%)")
print(f"Total with 3 annotations: {annotation_counts[3]} ({percentages[3]:.2f}%)")

if annotation_counts['more']:
    print(f"Total with more than 3 annotations: {len(annotation_counts['more'])} (IDs: {', '.join(map(str, annotation_counts['more']))})")
else:
    print("Total with more than 3 annotations: 0")