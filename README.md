## `Annotation Website/`

This folder contains a simple PHP- and JavaScript-based web platform used for manually annotating Maltese-language sentences with sentiment labels.

### Functionality

1. **Sentence Presentation**
   Up to 3 sentences at a time are displayed to users, selected from the shared dataset `combined_data.json`.

2. **Annotation Logic**

   * Sentences are selected based on:

     * Having fewer than `ANNOTATION_THRESHOLD` (currently 3) annotations.
     * Being marked as ambiguous (i.e., no clear majority sentiment).
   * User identity is managed with a browser cookie.
   * Sentence order is randomized within priority groups.

3. **Annotation Submission**

   * Annotations are sent via `api_annotate.php` and stored directly in `combined_data.json`, including sentiment label, timestamp, and user ID.

4. **Progress Feedback**

   * Users receive visual feedback on annotation progress within the batch.

5. **Post-Processing Scripts**

   * Python scripts help analyze and export the annotation data for training and evaluation.

---

### Project Structure

| File/Folder                    | Description                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------- |
| `index.php`                    | Main langing page of the website with project overview, consent form, and link to annotation interface.          |
| `annotationPage.php`           | Main annotation interface. Implements sentence selection and user interaction.               |
| `api_annotate.php`             | Backend endpoint for saving annotations. Handles user ID tracking via cookies.               |
| `finishPage.php`               | Thank-you page shown after users opt to stop annotating.                                     |
| `combined_data.json`           | Master data file containing all sentences and their annotation metadata.                     |
| `analysis.py`                  | Prints statistics (e.g., annotation counts per sentence) from `combined_data.json`.          |
| `saveAnnotations.py`           | Exports sentences with clear majority sentiment (including neutral) to `annotated_data.csv`. |
| `saveAnnotationsNoNeutrals.py` | Same as above, but excludes sentences with a neutral majority.                               |
| `static/css/styles.css`        | Stylesheet for the website (assumed).                                                        |
| `static/js/script.js`          | Handles button actions and API calls on the annotation page.                                 |
| `UM Logo.png`                  | University of Malta logo (for branding).                                                     |

---

### 👣 User Flow

1. User opens `index.php` and agrees to participate.
2. They proceed to `annotationPage.php`, which loads up to 3 unannotated or ambiguous sentences.
3. Clicking a sentiment button (e.g., **Pożittiv**, **Negattiv**, etc.) submits the response.
4. Data is sent via `script.js` → `api_annotate.php` → `combined_data.json`.
5. When finished, the user clicks **Ieqaf**, landing on `finishPage.php`.

---

### 🧪 Annotation Processing Scripts

After collecting annotations, you can generate clean datasets using the following scripts:

* **View statistics**:

  ```bash
  python analysis.py
  ```

* **Export with all majority sentiments (incl. neutral)**:

  ```bash
  python saveAnnotations.py
  ```

* **Export excluding neutral**:

  ```bash
  python saveAnnotationsNoNeutrals.py
  ```

These scripts produce CSV files that can be used for training and evaluation.

---

## `Scrapers/` Directory

This directory contains all the scraping and preprocessing scripts used to collect and prepare data for Maltese sentiment analysis. The content here was developed by **Ian** and **Matthew**.

### Top-Level Notebooks

* **`RedditScraper.ipynb`**
    Developed by Ian. This notebook is designed to scrape comments from a predefined list of Reddit posts.

    To use it:
    1.  Enter your Reddit API credentials within the notebook.
    2.  Populate the `post_ids` list with the IDs of the Reddit posts you wish to scrape.
    3.  Execute all cells in the notebook.

    The extracted comments will be saved to a JSON file named `reddit_comments.json`.

* **`Youtube_scraper.ipynb`**
    Developed by Ian. This notebook is designed to scrape comments from all videos of a specified YouTube channel.

    To use it:
    1.  Enter your YouTube Data API key in the `api_key` variable.
    2.  Specify the `channel_username` for the YouTube channel you want to scrape.
    3.  You can adjust the `max_comments` parameter within the `get_comments` function to control how many comments are fetched per video (default is 1000).
    4.  Run all cells in the notebook.

    The scraped comments will be saved to a JSON file named after the `channel_username` (e.g., `JonMalliaPodcast.json`).
---

### `Facebook Scraper and Data Cleaning Pipeline/` Folder

This is a complete Facebook scraping and data preprocessing pipeline developed by **Matthew**. It includes the following components:

#### Main Scripts

* **`main.py`**
  This is the entry point to the Facebook data pipeline. Running this script will:

  1. Scrape data from the configured Facebook groups.
  2. Save the raw data in JSON format under `data/01_raw/`.
  3. Automatically run the full preprocessing pipeline, generating outputs in the following subfolders (see below).

* **`config.py`**
  Holds the configuration settings such as:

  * Paths to data directories.
  * URLs or IDs of Facebook groups to scrape.

#### `classes/` Folder

* **`cleaning.py`**
  Contains the preprocessing pipeline for cleaning and transforming raw JSON data (e.g., text normalization, filtering, anonymization steps).

* **`scraper.py`**
  Contains the logic for logging into and scraping content from Facebook groups.

* **`names/` Folder**

  * `names.txt` and `surnames.txt`
    Used for anonymizing personal names in scraped text data.

#### `data/` Folder

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

### How to Use

Running `main.py` will automatically:

* Scrape Facebook data (based on `config.py`)
* Apply all preprocessing steps
* Output the final dataset to `data/06_final/combined_data.json`

---
