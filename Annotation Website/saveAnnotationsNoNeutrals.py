import json
import csv

def saveAnnotations(json_file, output_csv):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    skipped_ids = []
    pos_count = neg_count = 0

    for entry in data:
        positive = entry.get("positive", 0)
        neutral = entry.get("neutral", 0)
        negative = entry.get("negative", 0)
        ma_nafx = entry.get("ma nafx", 0)

        total_votes = positive + neutral + negative + ma_nafx

        # Skip if fewer than 3 total votes
        if total_votes < 3:
            skipped_ids.append(entry["id"])
            continue

        # Get vote counts in a dictionary for easier analysis
        vote_counts = {
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "ma nafx": ma_nafx
        }

        # Find the label(s) with the highest votes
        max_votes = max(vote_counts.values())
        majority_labels = [label for label, count in vote_counts.items() if count == max_votes]

        # Skip if there's no unique majority or majority is "ma nafx" or "neutral"
        if len(majority_labels) != 1 or majority_labels[0] in ["ma nafx", "neutral"]:
            skipped_ids.append(entry["id"])
            continue

        # Assign numerical sentiment
        if majority_labels[0] == "positive":
            sentiment = 1
            pos_count += 1
        elif majority_labels[0] == "negative":
            sentiment = 0
            neg_count += 1

        entry["sentiment"] = sentiment

    # Write the filtered data to CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        for entry in data:
            if entry.get("sentiment") is not None:
                writer.writerow([entry["sentiment"], entry["content"]])

    print(f"Results saved to {output_csv}")

    print(f"Positive: {pos_count}")
    print(f"Negative: {neg_count}")
    print(f"Skipped due to insufficient/unclear votes: {len(skipped_ids)}")
    # print(f"Skipped IDs: {skipped_ids}")

# Example usage
json_file = "combined_data.json"
output_csv = "annotated_data(No Neutrals).csv"
saveAnnotations(json_file, output_csv)