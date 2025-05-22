import os

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Root data directory
DATA_DIR = os.path.join(BASE_DIR, "data") # /data

# Dictionary mapping different stages of the data processing pipeline to their respective paths
DATA_DIRECTORIES = {
    "root": DATA_DIR, # Root data directory
    "raw": os.path.join(DATA_DIR, "01_raw"), # Unprocessed raw data
    "cleaned": os.path.join(DATA_DIR, "02_cleaned"), # Data after initial cleaning
    "anonymized": os.path.join(DATA_DIR, "03_anonymized"), # Data with sensitive info removed
    "sentences": os.path.join(DATA_DIR, "04_sentences"), # Data split into sentences
    "maltese": os.path.join(DATA_DIR, "05_maltese"), # Data filtered to include only Maltese sentences
    "final": os.path.join(DATA_DIR, "06_final"), # Final dataset ready for use
}

# Ensure directories exist
for directory in DATA_DIRECTORIES.values():
    os.makedirs(directory, exist_ok=True)
    
# Facebook scraping configuration
FACEBOOK_GROUPS = [
    "https://www.facebook.com/groups/RUBS.Malta"
]

POST_LIMIT_PER_GROUP = 10  # Number of posts to fetch per group