## `Annotation Website/` Directory

This folder (developed by Fabio) contains a simple PHP and JavaScript-based web platform used for manually annotating Maltese-language sentences with sentiment labels.

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
| `index.php`                    | Main landing page of the website with project overview, consent form, and link to annotation interface.          |
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

### User Flow

1. User opens `index.php` and agrees to participate.
2. They proceed to `annotationPage.php`, which loads up to 3 unannotated or ambiguous sentences.
3. Clicking a sentiment button (e.g., **Pożittiv**, **Negattiv**, etc.) submits the response.
4. Data is sent via `script.js` → `api_annotate.php` → `combined_data.json`.
5. When finished, the user clicks **Ieqaf**, landing on `finishPage.php`.

---

### Annotation Processing Scripts

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

### Running the Annotation Website Locally
To run the annotation platform on your machine:

#### Requirements

PHP installed (e.g., via XAMPP, MAMP, or native install),
Python (for processing scripts),

#### Using PHP’s built-in server (Recommended for testing)

```bash
cd "Annotation Website"
php -S localhost:8000
```

Then open your browser and go to:
[http://localhost:8000/index.php](http://localhost:8000/index.php)

---

## `Machine Learning Algorithms/` Directory

This directory contains all the model development notebooks, training datasets, and finalized models used for Maltese sentiment analysis. Each subfolder represents a complete workflow for a specific algorithm.

---

### Subfolders Overview

| Folder           | Model                        | Developer |
| ---------------- | ---------------------------- | --------- |
| `Naive Bayes/`   | Naive Bayes Classifier       | Matthew   |
| `Random Forest/` | Random Forest Classifier     | Fabio     |
| `SVM/`           | Support Vector Machine (SVM) | Ian       |

---

### `Naive Bayes/`

This folder contains the full pipeline for training and using a Naive Bayes sentiment classifier.

**Files:**

* `01_Data_Preprocessing_And_Exploration.ipynb` – Initial EDA and data cleaning.
* `02_Model_Training_and_Evaluation.ipynb` – Trains the model, evaluates its performance.
* `03_Model_Finalization_and_Serialization.ipynb` – Finalizes preprocessing steps and exports the model.
* `04_Model_Usage_Demonstration.ipynb` – Demonstrates how to load and use the trained model.
* `naive_bayes_maltese_sentiment_analyzer.joblib` – Serialized scikit-learn pipeline model.
* `preprocessor.py` – Contains the `MalteseTextPreprocessor` class used in the pipeline.
* `data/` – Multiple versions of the datasets with different preprocessing configurations.
* `names/` – `names.txt` and `surnames.txt`, used for anonymization purposes.

---

### `Random Forest/`

This folder contains training, evaluation, and export scripts for a Random Forest classifier, alongside supporting data.

**Key Files:**

* `Random Forest.ipynb` – Performs data loading, preprocessing, training, and evaluation.
* `randomForestModel_Extended.pkl` – Trained Random Forest model.
* `vectorizer_Extended.pkl` – Fitted vectorizer (e.g., TF-IDF or CountVectorizer) used during training.
* `Sentiment CSVs/` – Cleaned and preprocessed datasets:

  * `crowdsourced_dataset_lowercased_lemmatized.csv`
  * `jerbarnes_dataset_lowercased_lemmatized.csv`

---

### `SVM/`

This folder mirrors the structure of the Naive Bayes folder, tailored for a Support Vector Machine classifier.

**Key Files:**

* `02_Model_Training_and_Evaluation_SVM.ipynb` – Trains and evaluates the SVM model.
* `03_Model_Finalization_and_Serialization.ipynb` – Saves the trained pipeline.
* `04_Model_Usage_Demonstration.ipynb` – Shows how to load and use the SVM model.
* `svm_maltese_sentiment_analyzer.joblib` – Final trained SVM model with preprocessing pipeline.
* `preprocessor.py` – Same preprocessing class used as in Naive Bayes.
* `data/` – Preprocessed dataset files used for training:

  * `crowdsourced_dataset_selective_lowercased_lemmatized.csv`
  * `jerbarnes_dataset_selective_lowercased_lemmatized.csv`

---

### Dataset Sources

Two primary datasets were used across all models:

* **Crowdsourced Dataset** – Collected via the annotation website (`combined_data.json` → CSV).
* **JerBarnes Dataset** – Pre-collected Maltese language dataset with labeled sentiment.

Each dataset has several variants based on preprocessing options:

* Lowercased vs. Selective Lowercased
* With or Without Lemmatization

---

## `Scrapers/` Directory

This directory contains all the scraping and preprocessing scripts used to collect and prepare data for Maltese sentiment analysis. The content here was developed by Ian and Matthew.

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

## `Web-based Demo/` — Directory

This folder contains a web-based demo application built using Flask that allows users to input Maltese text and receive real-time sentiment predictions from three different machine learning models: Naive Bayes, Random Forest, and SVM.

This demo serves as a user-friendly way to explore how the models classify sentiment.

---

### Folder Structure

| Path              | Description                                                               |
| ----------------- | ------------------------------------------------------------------------- |
| `app.py`          | Main Flask app. Serves pages and handles inference using selected models. |
| `preprocessor.py` | Custom Maltese text preprocessing functions used by Random Forest model.  |
| `models/`         | Contains all trained sentiment analysis models and vectorizers.           |
| `static/`         | Static assets (CSS and JS).                                               |
| `templates/`      | HTML templates used by the Flask frontend.                                |

---

### Models Overview

#### Naive Bayes (Matthew)

* File: `naive_bayes_maltese_sentiment_analyzer.joblib`
* Wrapped in a `scikit-learn` pipeline.
* Uses `MalteseTextPreprocessor` class for text cleaning and lemmatization.
* Prediction and preprocessing are handled within the pipeline.

#### Random Forest (Fabio)

* Files: `randomForestModel_Extended.pkl` and `vectorizer_Extended.pkl`
* Preprocessing is handled *manually* in `app.py` via functions from `preprocessor.py`:

  * `emoji_to_text()`
  * `tokenise()`
  * `clean_tokens()`
  * `selective_lowercase()`
  * `get_lemma()` (uses MLRS Gabra API)
* Vectorized with `vectorizer_Extended.pkl`.

#### SVM (Ian)

* File: `svm_maltese_sentiment_analyzer.joblib`
* Also a `scikit-learn` pipeline.
* Uses the same `MalteseTextPreprocessor` as Naive Bayes.

---

### User Interface (Frontend)

* **`analyze.html`** – Main interface with input box, model selector, and result display.
* **`layout.html`** – Base template for page layout.
* **CSS/JS** – Located in `static/css/styles.css` and `static/js/script.js`.

---

### Running the Demo

To run the Flask web app:

```bash
cd "Web-based Demo"
python app.py
```

Then navigate to `http://127.0.0.1:5000` in your browser.

---

### How It Works

1. User enters text and selects a model.
2. `app.py` processes the request:

   * Uses pipeline or manual preprocessing.
   * Predicts sentiment (positive/negative).
   * Computes confidence score (if available).
3. The result is displayed:

   * Input text
   * Preprocessed text
   * Predicted sentiment
   * Confidence level
   * Model used

---
