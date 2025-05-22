from classes.scraper import FacebookScraper
from classes.cleaning import TextCleaner, TextAnonymizer, MalteseFilter, SentenceSplitter, JsonCombiner
from config import DATA_DIRECTORIES as DIRS
from config import FACEBOOK_GROUPS, POST_LIMIT_PER_GROUP

for group in FACEBOOK_GROUPS:
    scraper = FacebookScraper(group_url=group, num_posts=POST_LIMIT_PER_GROUP, debug=True, output_dir=DIRS["raw"])
    scraper.scrape()

cleaner = TextCleaner(DIRS["raw"], DIRS["cleaned"])
cleaner.process_directory()

anonymizer = TextAnonymizer(DIRS["cleaned"], DIRS["anonymized"])
anonymizer.process_directory()

sentence_splitter = SentenceSplitter(DIRS["anonymized"], DIRS["sentences"])
sentence_splitter.process_directory()

language_filter = MalteseFilter(DIRS["sentences"], DIRS["maltese"])
language_filter.process_directory()

combiner = JsonCombiner(DIRS["maltese"], DIRS["final"], output_file="combined_data.json")
combiner.process_directory()