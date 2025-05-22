from emoji import demojize
import malti.tokeniser
import requests
import time
from functools import lru_cache
from collections import OrderedDict
from abc import ABC, abstractmethod
import json
import os
from langid.langid import LanguageIdentifier, model
from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
import re
from emoji import demojize

# =============
# Model Loading
# =============

# MalteseTokenizer without Maltese language filtering
class MalteseTokenizer:
    def __init__(self, case_folding_type=2, lemmatize=True):
        if case_folding_type not in {0, 1, 2}:
            raise ValueError("Invalid case folding method. Choose from 0 (no change), 1 (lowercase everything except fully-uppercase words), 2 (full lowercasing)")
        self.case_folding_type = case_folding_type
        self.lemmatize = lemmatize

        self.cleaner = TextCleaner(input_dir=None, output_dir=None)
        self.anonymizer = TextAnonymizer(input_dir=None, output_dir=None, names_dir='./names')
        
    def __call__(self, text):
        # Apply the same initial cleaning steps used in the Facebook Scraper dataset
        text = self.cleaner.clean_text(text)
        text = self.anonymizer.anonymize_text(text)

        # Apply preprocessing steps
        text = emoji_to_text(text)
        tokens = tokenise(text)
        tokens = clean_tokens(tokens)
        if self.case_folding_type == 1:
            tokens = selective_lowercase(tokens)
        elif self.case_folding_type == 2:
            tokens = lowercase(tokens)
        tokens = [normalize_word(token) for token in tokens]
        if self.lemmatize:
            tokens = [get_lemma(token) for token in tokens]
        return tokens


class MalteseTextPreprocessor(BaseEstimator, TransformerMixin):
    """
    Scikit-learn compatible transformer for applying the MalteseTokenizer.
    """
    def __init__(self, case_folding_type=2, lemmatize=True):
        self.case_folding_type = case_folding_type
        self.lemmatize = lemmatize
        # Instantiate the tokenizer when the transformer is created
        self.tokenizer_ = MalteseTokenizer(case_folding_type=self.case_folding_type, 
                                           lemmatize=self.lemmatize)

    def fit(self, X, y=None):
        return self # No fitting needed for this preprocessor

    def transform(self, X, y=None):
        processed_X = []
        for raw_text in X: # X is an iterable of raw text strings
            tokens = self.tokenizer_(raw_text) 
            processed_X.append(' '.join(tokens) if tokens else "")
        return pd.Series(processed_X) # Output a Series for the next pipeline step

# ==================
# Text Preprocessing
# ==================

def emoji_to_text(text):
    """
    Replaces emojis and common emoticons in a string with their text equivalents.
    Handles emoticons with repeated ending characters (e.g., :)))), :-)))), xDDDD).
    
    Args:
        text: The text containing emojis and emoticons to process
    """
    result = text

    # Replace emojis
    result = demojize(result)

    # Define emoticon patterns with regex
    emoticon_patterns = {
        # Happy/Positive
        r":\)+": ":smile:",
        r":-\)+": ":smile:",
        r":D+": ":big smile:",
        r":-D+": ":big smile:",
        r"=\)+": ":smile:",
        r"=D+": ":big smile:",
        r"<3+": ":heart:",
        r":\*+": ":kiss:",
        r":-\*+": ":kiss:",
        r";\)+": ":wink:",
        r";-\)+": ":wink:",
        r":P+": ":tongue:",
        r":-P+": ":tongue:",
        r":p+": ":tongue:",
        r"=P+": ":tongue:",
        r":-p+": ":tongue:",
        r"x[Dd]+": ":laughing:",
        r"X[Dd]+": ":laughing:",
        
        # Sad/Negative
        r":\(+": ":sad:",
        r":-\(+": ":sad:",
        r"D:+": ":sad:",
        r":/+": ":skeptical:",
        r":\\+": ":skeptical:",
        r":\|+": ":neutral:",
        r":-\|+": ":neutral:",
        r":O+": ":surprised:",
        r":o+": ":surprised:",
        r":'-\(+": ":crying:",
        r"-_-+": ":annoyed:",
    }
    
    # Replace each emoticon pattern with its text equivalent
    for pattern, replacement in emoticon_patterns.items():
        result = re.sub(pattern, replacement, result)
        
    return result

# ===============================
# Tokenisation & Token Processing
# ===============================

def tokenise(text):
    # Tokenises text into a list of tokens
    return malti.tokeniser.tokenise(text)


def clean_tokens(tokens):
    """
    Cleans and normalizes punctuation within a list of tokens.
    
    Args:
        tokens: The list of tokens to clean
    """
    result = []
    i = 0
    
    while i < len(tokens):
        # Skip empty tokens
        if not tokens[i]:
            i += 1
            continue

        # Handle three or more consecutive dots ('.', '.', '.' -> '...')
        if (i <= len(tokens) - 3 and 
            tokens[i] == '.' and 
            tokens[i+1] == '.' and 
            tokens[i+2] == '.'):
            result.append('...')
            while i < len(tokens) and tokens[i] == '.':
                i += 1
            continue
            
        # Handle emoji patterns (':', 'thumbs_up', ':' -> ':thumbs_up:')
        if (i <= len(tokens) - 3 and 
            tokens[i] == ':' and 
            tokens[i+2] == ':'):
            result.append(f":{tokens[i+1]}:")
            i += 3
            continue

        # Handle placeholder patterns ('[', 'NAME', ']' -> '[NAME]')
        if (i <= len(tokens) - 3 and 
            tokens[i] == '[' and 
            tokens[i+2] == ']'):
            result.append(f"[{tokens[i+1]}]")
            i += 3
            continue
        
        # Handle !? combination ('!', '?' -> '!?')
        if (i <= len(tokens) - 2 and 
            tokens[i] == '!' and 
            tokens[i+1] == '?'):
            result.append('!?')
            i += 2
            continue
            
        # Handle two or more consecutive exclamation marks ('!', '!' -> '!!')
        if (i <= len(tokens) - 2 and 
            tokens[i] == '!' and 
            tokens[i+1] == '!'):
            result.append('!!')
            while i < len(tokens) and tokens[i] == '!':
                i += 1
            continue
            
        # Handle two or more consecutive question marks ('?', '?' -> '??')
        if (i <= len(tokens) - 2 and 
            tokens[i] == '?' and 
            tokens[i+1] == '?'):
            result.append('??')
            while i < len(tokens) and tokens[i] == '?':
                i += 1
            continue

        # Remove '-' at end of tokens ('bil-' -> 'bil')
        # Helps model generalize since many articles in our dataset are written without hyphens
        # (e.g. "bil Malti" instead of "bil-Malti")
        if tokens[i].endswith('-'):
            tokens[i] = tokens[i][:-1]

        # Add any other token as is
        result.append(tokens[i])
        i += 1
    
    # Remove any blank tokens from the final result
    result = [token for token in result if token.strip()]

    return result

def lowercase(tokens):
    """
    Converts all tokens to lowercase, except placeholder tokens (e.g. [NAME]).
    
    Args:
        tokens: The list of tokens to convert to lowercase
    """
    return [token if (token.startswith('[') and token.endswith(']')) else token.lower() for token in tokens]

def selective_lowercase(tokens):
    """
    Converts tokens to lowercase, but keeps fully uppercase words and placeholder tokens unchanged.
    
    Args:
        tokens: The list of tokens to selectively convert to lowercase
    """
    return [token if token.isupper() or (token.startswith('[') and token.endswith(']')) 
            else token.lower() for token in tokens]

def tokenise_with_pos_tag(text):
    """
    Tokenises and POS-tags a Maltese text using the MLRS API.
    
    Args:
        text: The text to tokenize and tag with parts of speech
    """
    url = "https://mlrs.research.um.edu.mt/tools/mlrsapi/tag"
    
    # Parameters for the GET request
    params = {
        'text': text
    }

    try:
        # Make the GET request
        response = requests.get(url, params=params)
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Get the JSON response and return the result
        json_response = response.json()
        return json_response['result']
        
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during POS tagging: {e}")
        return None
    
# =============
# Lemmatisation
# =============
    
@lru_cache(maxsize=512)
def make_request(url):
    """
    Helper function to make request with retry logic.
    
    Args:
        url: The URL to make the request to
    """
    DELAY = 3  # 3 second delay between requests
    MAX_RETRIES = 3  # Will try each request up to 3 times

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                time.sleep(DELAY)  # Wait before making request after first attempt

            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt == MAX_RETRIES - 1:  # Last attempt
                print(f"Request failed after {MAX_RETRIES} attempts: {e}")
                print(f"URL: {url}")
                return None
            print(f"Request failed, retrying: {e}")

def normalize_word(word):
    """
    Takes an incorrectly written Maltese word (e.g., 'nohorgu') and uses Gabra's Search Suggest API
    to try to find its proper spelling equivalent ('noħorġu').
    
    Args:
        word: The word to normalize
    """
    # Skip empty words    
    if not word:
        return ""
    
    # Skip if word is too short
    if len(word) < 2:
        return word

    # Skip if word isn't alphanumeric
    if not word.isalnum():
        return word
        
    # Special case - avoid 'hemm' being converted to 'ħemm'
    if word == 'hemm':
        return word

    # Store original word case pattern
    is_upper = word.isupper()
    is_title = word.istitle()
    
    # Try searching wordforms first
    url = f"https://mlrs.research.um.edu.mt/resources/gabra-api/wordforms/search_suggest?s={word.lower()}"
    data = make_request(url)
    
    if data and data.get("results") and len(data["results"]) > 0:
        # Iterate through all wordform results
        for result in data["results"]:
            if "wordform" in result and "surface_form" in result["wordform"]:
                surface_form = result["wordform"]["surface_form"]
                
                # Apply original case pattern and return
                if is_upper:
                    return surface_form.upper()
                elif is_title:
                    return surface_form.title()
                return surface_form
    
    # If not found, try searching lexemes
    url = f"https://mlrs.research.um.edu.mt/resources/gabra-api/lexemes/search_suggest?s={word.lower()}"
    data = make_request(url)
    
    if data and data.get("results") and len(data["results"]) > 0:
        # Iterate through all lexeme results
        for result in data["results"]:
            if "lexeme" in result and "lemma" in result["lexeme"]:
                lemma = result["lexeme"]["lemma"]
                
                # Only use lemma if it's the same length as the input word
                if len(lemma) == len(word):
                    if is_upper:
                        return lemma.upper()
                    elif is_title:
                        return lemma.title()
                    return lemma
    
    # If no matches found, return original word
    return word

def get_lemma(word):
    """
    Retrieves the lemma (base form) of a given word using the Gabra API.
    
    Args:
        word: The word to lemmatize
    """
    # Skip empty words
    if not word:
        return ""

    # Skip if word is too short
    if len(word) < 2:
        return word

    # Skip if word isn't alphanumeric
    if not word.isalnum():
        return word

    # Store original word case pattern
    is_upper = word.isupper()
    is_title = word.istitle()
    
    url = f"https://mlrs.research.um.edu.mt/resources/gabra-api/lexemes/lemmatise?s={word.lower()}"
    data = make_request(url)

    # Check if results exist and are not empty
    if data and data.get("results") and len(data["results"]) > 0:
        # Iterate through all results
        for result in data["results"]:
            surface_form = result["wordform"]["surface_form"]
            
            # Check if surface form matches and lexeme/lemma exists
            if (word.lower() == surface_form and 
                "lexeme" in result and 
                "lemma" in result["lexeme"]):
                
                lemma = result["lexeme"]["lemma"]
                
                # Apply original case pattern to lemma
                if is_upper:
                    return lemma.upper()
                elif is_title:
                    return lemma.title()
                return lemma

    # No matching lemma found, return the original word
    return word

# =======================================================
# Classes imported from Facebook Post Processing Pipeline
# =======================================================

class TextProcessor(ABC):
    """
    Abstract base class for processing JSON files containing posts.
    """
    def __init__(self, input_dir, output_dir=None):
        self.input_dir = input_dir
        self.output_dir = output_dir or input_dir

    @abstractmethod
    def process(self, data):
        """
        Process a list of posts.
        
        Args:
            data: List of post dictionaries
        
        Returns:
            Processed list of post dictionaries.
        """
        pass

    def process_directory(self):
        """Process all JSON files in the input directory."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        for filename in os.listdir(self.input_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.input_dir, filename)
                self._process_file(file_path)

    def _process_file(self, file_path):
        """Load JSON, process it, and save the result."""
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        processed_data = self.process(data)

        if processed_data:
            output_path = os.path.join(self.output_dir, os.path.basename(file_path))
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(processed_data, file, ensure_ascii=False, indent=4)
            print(f"Processed {file_path} and saved to {output_path}")
        else:
            print(f"No valid data in {file_path}")

class MalteseFilter(TextProcessor):
    def __init__(self, input_dir, output_dir=None, threshold=0.94, debug=False):
        super().__init__(input_dir, output_dir)

        self.threshold = threshold
        self.debug = debug

        self.identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        self.identifier.set_languages(['en', 'mt'])

    def is_maltese(self, text):
        """
        Check if text is potentially Maltese (i.e., not confidently English)
        
        Args:
            text: String to analyze
            
        Returns:
            bool: True if text should be kept (potentially Maltese), False if confidently English
            tuple: (language, probability) if debug is enabled, None otherwise
        """
        if not text:
            return True, None
            
        lang, prob = self.identifier.classify(text)
        lang_info = (lang, prob)
        is_english = (lang == 'en' and prob > self.threshold)
        
        return not is_english, lang_info

    def process(self, data):
        filtered_posts = []
        
        for post in data:
            content = post.get('content', '')
            is_maltese, lang_info = self.is_maltese(content)
            
            if is_maltese:
                if self.debug:
                    post['lang_info'] = lang_info
                filtered_posts.append(post)
                
        return filtered_posts

class TextCleaner(TextProcessor):
    """
    Preprocessor that cleans and normalizes text content in posts.
    """
    def __init__(self, input_dir, output_dir=None):
        super().__init__(input_dir, output_dir)

    def clean_text(self, text):
        """
        Clean and normalize a single text string.
        
        Args:
            text: Input text string
            
        Returns:
            Cleaned text string
        """

        if not isinstance(text, str) or not text:
            return text
        
        # Replace square brackets with round brackets (square brackets are reserved for placeholders)
        text = text.replace("[", "(")
        text = text.replace("]", ")")

        # Catch URLs and Emails and replace them with a placeholder (to be restored after cleaning)
        # This avoids full stops (.) in URLs and emails to be mistaken for sentence boundaries
        urls = re.findall(TextAnonymizer.PATTERNS['[URL]'], text) # Catch URLs
        emails = re.findall(TextAnonymizer.PATTERNS['[EMAIL]'], text) # Catch emails

        # Replace URLs with placeholders
        for i, url in enumerate(urls):
            text = text.replace(url, f'[URL_CLEANING_PLACEHOLDER_{i}]')

        # Replace emails with placeholders
        for i, email in enumerate(emails):
            text = text.replace(email, f'[EMAIL_CLEANING_PLACEHOLDER_{i}]')

        # Replace curly quotes with straight quotes
        text = text.replace("’", "'")
        text = text.replace("‘", "'")

        text = text.replace("“", '"')
        text = text.replace("”", '"')

        # Replace punctuation emojis with their text equivalent (required for sentence splitting in later steps)
        text = text.replace("⁉️", "!?")
        text = text.replace("‼️", "!!")
        text = text.replace("❓", "?")
        text = text.replace("❔", "?")
        text = text.replace("❗", "!")
        text = text.replace("❕", "!")

        # Handle newlines first
        text = re.sub(r'\s*\\n\s*', ' ', text)
        
        text = re.sub(r'\.{2,}', '...', text)  # ANY sequence of 2+ dots are converted to 3 dots
        
        # Normalize multiple punctuation marks to maximum of 2 consecutive marks
        text = re.sub(r'!{2,}', '!!', text)     # Replaces 2+ exclamation marks with 2 exclamation marks
        text = re.sub(r'\?{2,}', '??', text)    # Replaces 2+ question marks with 2 question marks
        text = re.sub(r'(?:(?=[!?]*\?[!?]*!|(?=[!?]*![!?]*\?))[!?]+)', '!?', text) # Replaces 2+ !? and question marks with !?

        # Fix spacing after punctuation (excluding numbers)
        text = re.sub(r'(?<!\d)([.!?,])(?=[^\s])', r'\1 ', text)
        
        # Fix specific case of wrapped text with trailing punctuation
        text = re.sub(r'\s+([.!?,])(?=\s|$)', r'\1', text)

        # Remove space between full stops and closing paranthesis
        text = re.sub(r'\.\s+\)', '.)', text)

        # Clean up any multiple spaces  
        text = re.sub(r'\s+', ' ', text)
        
        # Restore URLs
        for i, url in enumerate(urls):
            text = text.replace(f'[URL_CLEANING_PLACEHOLDER_{i}]', url)

        # Restore emails
        for i, email in enumerate(emails):
            text = text.replace(f'[EMAIL_CLEANING_PLACEHOLDER_{i}]', email)

        return text.strip()
    
    def process(self, data):
        """
        Process list of posts by cleaning their content.
        
        Args:
            data: List of post dictionaries
            
        Returns:
            List of posts with cleaned content
        """
        processed_data = []
        for post in data:
            if 'content' in post and post['content']:
                cleaned_post = post.copy()
                cleaned_post['content'] = self.clean_text(post['content'])
                processed_data.append(cleaned_post)
                
        return processed_data

class TextAnonymizer(TextProcessor):
    """
    Preprocessor that anonymizes text by replacing identifiers with placeholders.
    """

    # Ordered to prevent partial replacements
    PATTERNS = OrderedDict([
            # ([Placeholder], Pattern)
            ('[URL]', r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F])|[/?=&])+'),
            ('[EMAIL]', r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            ('[PHONE]', r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}'),
            ('[USER]', r'@\w+')])

    def __init__(self, input_dir, output_dir=None, names_dir='./classes/names/'):
        super().__init__(input_dir, output_dir)

        # Names and surnames in the list that caused false positives when filtering
        NAME_BLACKLIST = [
            'vera', 'mara', 'beda', 'tan', 'dawn', 'fortunata', 'all', 'tipo', 'white', 'gili', 'shana', 'quick', 'bin', 'ili', 'kind', 'venera', 'madonna', 'mia', 'best', 'king', 'kind', 'din', 'gili'
        ]

        # Load names and surnames
        try:
            if names_dir.endswith('/'):
                names_dir = names_dir.rstrip('/')

            with open(f'{names_dir}/names.txt', 'r', encoding='utf-8') as f:
                names = [line.strip() for line in f if line.strip()]
            
            with open(f'{names_dir}/surnames.txt', 'r', encoding='utf-8') as f:
                surnames = [line.strip() for line in f if line.strip()]

            # Remove duplicates
            names = list(set(names))
            surnames = list(set(surnames))

            # Filter out unwanted names
            names = [name for name in names if name.lower() not in NAME_BLACKLIST]
            surnames = [surname for surname in surnames if surname.lower() not in NAME_BLACKLIST]

            # Keep only names longer than 2 characters
            names = [name for name in names if len(name) > 2]
            surnames = [surname for surname in surnames if len(surname) > 2]

        except Exception as e:
            print(f"Error loading name files: {e}")
            names = []
            surnames = []
        
        # Create name patterns
        if names and surnames:
            name_pattern = r'(?i)\b(?:' + '|'.join(re.escape(name) for name in names) + r')\b'
            surname_pattern = r'(?i)\b(?:' + '|'.join(re.escape(surname) for surname in surnames) + r')\b'

            # Ordered to prevent partial replacements
            self.PATTERNS['[NAME]'] = name_pattern
            self.PATTERNS['[SURNAME]'] = surname_pattern

    def anonymize_text(self, text):
        """
        Anonymize a single text string.
        
        Args:
            text: Input text string
            
        Returns:
            Cleaned text string
        """
        if not isinstance(text, str) or not text:
            return text
        
        for replacement, pattern in self.PATTERNS.items():
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def process(self, data):
        """
        Process list of posts by anonymizing their content.
        
        Args:
            data: List of post dictionaries
            
        Returns:
            List of posts with anonymized content
        """
        processed_data = []
        for post in data:
            if 'content' in post and post['content']:
                anonymized_post = post.copy()
                anonymized_post['content'] = self.anonymize_text(post['content'])
                processed_data.append(anonymized_post)
                
        return processed_data
    
