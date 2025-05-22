import os
import json
from abc import ABC, abstractmethod
import string
from langid.langid import LanguageIdentifier, model
from pathlib import Path
import json
import os
import re
from collections import OrderedDict

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


class SentenceSplitter(TextProcessor):
    def __init__(self, input_dir, output_dir=None):
        super().__init__(input_dir, output_dir)

        # Create regex pattern which matches any placeholder from TextAnonymizer
        placeholder_types = '|'.join(key[1:-1] for key in TextAnonymizer.PATTERNS.keys())
        self.placeholder_regex = re.compile(f"\\[({placeholder_types})\\]")

    def split_sentences(self, text):
        # Common Maltese abbreviations and titles 
        abbreviations = {
            'Dr', 'Mr', 'Mrs', 'Ms', 'Prof', 'Profs', 'Dott', 'Onor', 'Kan',
            'S.L', 'Kap', 'Art', 'Fr', 'Sra', 'Sur', 'Sinjura', 'Sinj', 
            'et al', 'eċċ', 'ecc', 'e.g', 'i.e', 'vs', 'St', 'P.S'
        }

        # Create pattern for abbreviations to protect them
        abbrev_pattern = '|'.join(r'\b' + re.escape(abbr) + r'\.' for abbr in abbreviations)

        protected_text = text

        # Protect numbers with punctuation
        protected_text = re.sub(r'([€$]?\d+(?:[.,]\d+)?(?:-[€$]?\d+(?:[.,]\d+)?)?)', 
                            lambda m: f"NUM_{m.group(1).replace('.','DOT').replace(',','COMMA')}_MARK", 
                            protected_text)

        # Protect ellipses
        protected_text = re.sub(r'\.{3,}', 'ELLIPSIS_MARK', protected_text)

        # Protect abbreviations
        abbrev_matches = list(re.finditer(abbrev_pattern, protected_text))
        for i, match in enumerate(abbrev_matches):
            protected_text = protected_text.replace(match.group(), f"ABBREV_{i}_MARK")

        # Split on sentence endings or newlines, keeping the delimiters
        pattern = r'([.!?]+|\n+)'
        splits = re.split(pattern, protected_text)

        # Reconstruct sentences with their endings
        sentences = []
        for i in range(0, len(splits)-1, 2):
            if splits[i] or splits[i+1]:  # If either part is non-empty
                sentence = (splits[i] + splits[i+1]).strip()
                if sentence:
                    sentences.append(sentence)

        # Add the last part if it exists and wasn't followed by a delimiter
        if len(splits) % 2 == 1 and splits[-1].strip():
            sentences.append(splits[-1].strip())

        for i, sentence in enumerate(sentences):
            # Keep replacing until no more matches are found
            while 'NUM_' in sentences[i]:
                sentences[i] = re.sub(r'NUM_([^_]+)_MARK', 
                                    lambda m: m.group(1).replace('DOT', '.').replace('COMMA', ','), 
                                    sentences[i])

        # Restore ellipses
        for i, sentence in enumerate(sentences):
            sentences[i] = sentence.replace('ELLIPSIS_MARK', '...')

        # Restore abbreviations
        for i, match in enumerate(abbrev_matches):
            for j, sentence in enumerate(sentences):
                sentences[j] = sentence.replace(f"ABBREV_{i}_MARK", match.group())

        sentences = [sentence.strip() for sentence in sentences] # Remove leading or trailing whitespace
        sentences = [sentence[0].upper() + sentence[1:] for sentence in sentences] # Capitalize first letter of sentence

        return sentences

    def is_invalid_sentence(self, sentence):
        # If the sentence is empty or just whitespace
        if not sentence.strip():
            return True
        
        # If the sentence contains only punctuation or spaces
        if all(char in string.punctuation or char.isspace() for char in sentence):
            return True

        # If the sentence is only placeholders
        if not self.placeholder_regex.sub('', sentence).strip():
            return True

        return False


    def process(self, data):
        processed_data = []
        for post in data:
            sentences = self.split_sentences(post['content'])
            for i, sentence in enumerate(sentences):
                # Skip invalid sentences
                if self.is_invalid_sentence(sentence):
                    continue

                new_post = post.copy()
                new_post['sentence_number'] = i + 1
                new_post['content'] = sentence
                processed_data.append(new_post)
        return processed_data

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

class JsonCombiner:
    def __init__(self, input_dir, output_dir=None, output_file="combined_data.json"):
        self.input_dir = input_dir
        self.output_dir = output_dir or input_dir
        self.output_file = output_file
        self.content_hash_set = set()  # Track unique content hashes

    def _normalize_content(self, content):
        """Normalize content for comparison by removing extra whitespace and converting to lowercase"""
        return ' '.join(content.lower().split())

    def _hash_content(self, content):
        """Create hash of normalized content"""
        normalized = self._normalize_content(content)
        return hash(normalized)

    def process_directory(self):
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        combined_data = []
        sentence_id = 0
        
        # Process all json files
        for file_path in Path(self.input_dir).glob("*.json"):
            group_name = file_path.stem  # Get filename without extension
            
            # Read and process file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    content = item['content']
                    content_hash = self._hash_content(content)
                    
                    # Only add if content is unique
                    if content_hash not in self.content_hash_set:
                        combined_data.append({
                            'id': sentence_id,
                            'source': group_name,
                            'content': content
                        })
                        self.content_hash_set.add(content_hash)
                        sentence_id += 1
        
        # Log duplicate stats
        print(f"Saved {len(combined_data)} unique entries.")
        
        # Save combined data
        output_path = Path(self.output_dir) / self.output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=4, ensure_ascii=False)
        
        # Clean up original files if output is same as input 
        if self.output_dir == self.input_dir:
            for file_path in Path(self.input_dir).glob("*.json"):
                if file_path.name != self.output_file:
                    file_path.unlink()
