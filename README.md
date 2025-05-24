## 📁 `Scrapers/` Directory

This directory contains all the scraping and preprocessing scripts used to collect and prepare data for Maltese sentiment analysis. The content here was developed by **Ian** and **Matthew**.

### 📄 Top-Level Notebooks

* **`RedditScraper.ipynb`**
  Developed by Ian. This notebook scrapes Reddit comments using specific search queries or subreddit targets.

* **`Youtube_scraper.ipynb`**
  Developed by Ian. This notebook extracts comments from YouTube videos, optionally filtering by Maltese language content.

---

### 📁 `Facebook Scraper and Data Cleaning Pipeline/` Folder

This is a complete Facebook scraping and data preprocessing pipeline developed by **Matthew**. It includes the following components:

#### 📄 Main Scripts

* **`main.py`**
  This is the entry point to the Facebook data pipeline. Running this script will:

  1. Scrape data from the configured Facebook groups.
  2. Save the raw data in JSON format under `data/01_raw/`.
  3. Automatically run the full preprocessing pipeline, generating outputs in the following subfolders (see below).

* **`config.py`**
  Holds the configuration settings such as:

  * Paths to data directories.
  * URLs or IDs of Facebook groups to scrape.

#### 📁 `classes/` Folder

* **`cleaning.py`**
  Contains the preprocessing pipeline for cleaning and transforming raw JSON data (e.g., text normalization, filtering, anonymization steps).

* **`scraper.py`**
  Contains the logic for logging into and scraping content from Facebook groups.

* **`names/` Folder**

  * `names.txt` and `surnames.txt`
    Used for anonymizing personal names in scraped text data.

#### 📁 `data/` Folder

The full preprocessing pipeline generates data across the following stages:

1. **`01_raw/`** – Raw JSON data from:

   * Facebook scraper
   * YouTube scraper
   * Reddit scraper

2. **`02_cleaned/`** – Cleaned version of the raw data.

3. **`03_anonymized/`** – Text with names and surnames anonymized.

4. **`04_sentences/`** – Text split into individual sentences.

5. **`05_maltese/`** – Sentences filtered to include only those written in Maltese.

6. **`06_final/`** – Final merged dataset across platforms.

   * Contains `combined_data.json` with all preprocessed, anonymized, and filtered text.

---

### ✅ How to Use

Running main.py will automatically:

* Scrape Facebook data (based on `config.py`)
* Apply all preprocessing steps
* Output the final dataset to `data/06_final/combined_data.json`

---
