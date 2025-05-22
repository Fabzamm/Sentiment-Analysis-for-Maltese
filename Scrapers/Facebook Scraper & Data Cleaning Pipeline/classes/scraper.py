from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
import os

class FacebookScraper:
    def __init__(self, group_url, num_posts=10, debug=False, output_dir="output"):
        self.group_url = group_url.rstrip('/') # Remove trailing '/' for correct group name extraction
        self.num_posts = num_posts
        self.debug = debug
        self.output_dir = output_dir
        self.driver = self._init_driver()

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _debug_print(self, message):
        # Print debug messages if debug mode is enabled
        if self.debug:
            print(f"[DEBUG] {message}")

    def _init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        # Disable permission popups
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-geolocation")
        options.add_argument("--disable-media-stream")
        
        # Additional options to enhance privacy and reduce detection
        options.add_argument("--disable-infobars")
        options.add_argument("--start-maximized")
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.media_stream": 2
        })

        options.add_argument("--log-level=3")  # Suppress logs (INFO=0, WARNING=1, ERROR=2, FATAL=3)
        options.add_argument("--disable-logging")  # Disable logging

        # Set UTF-8 encoding for Chrome 
        options.add_argument('--lang=en-US')
        options.add_argument('--charset=UTF-8')

        return webdriver.Chrome(options=options)

    def open_group_page(self):
        try:
            print("Opening the Facebook group page...")
            self.driver.get(self.group_url)
            self._debug_print("Successfully opened Facebook group page.")

        except Exception as e:
            print(f"Error: Failed to open the group page: {e}")

    def wait_for_user_login(self):
        # Pause and wait for the user to log in manually
        print("Please log in to Facebook manually in the opened browser.")
        logged_in = False
        
        while not logged_in:
            input("Once you're logged in and on the group page, press Enter to start scraping...\n")
            current_url = self.driver.current_url
            
            if self.group_url in current_url:
                print("Login confirmed. Ready to scrape posts.")
                logged_in = True
            else:
                print(f"Warning: Current URL ({current_url}) doesn't match the configured URL ({self.group_url})")
                
                action = input("Would you like to:\n1. Proceed with current page\n2. Redirect to group page\nEnter choice (1-2): ").strip()
                
                if action == "1":
                    print("Proceeding with current page.")
                    logged_in = True
                elif action == "2":
                    self.driver.get(self.group_url)
                    self._debug_print("Redirected to the group page.")
                else:
                    print("Invalid choice. Please try again.")

    def scrape_posts(self):
        max_scroll_attempts = 5  # Number of additional scroll attempts if no new posts are found

        file_name = self.group_url.split('/')[-1] + '.json'
        file_path = os.path.join(self.output_dir, file_name)
        max_posts = self.num_posts
        post_counter = 0
        seen_posts = set()  # Track processed posts
        first_post = True  # Flag to track first post
        
        time.sleep(2)  # Initial wait time
        self._debug_print(f"Starting to scrape {max_posts} posts...")
        self._debug_print(f"Writing data to {file_path}.")

        with open(file_path, "w", encoding='utf-8') as file:
            file.write("[\n")  # Start JSON array
            file.flush()  # Flush the file buffer

            while post_counter < max_posts:
                # Find all story message divs
                story_divs = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-ad-rendering-role="story_message"]')
                self._debug_print(f"Found {len(story_divs)} story divs.")

                found_new_post = False
                for story_div in story_divs:
                    if post_counter >= max_posts:
                        break

                    post_id = str(hash(story_div))
                    if post_id in seen_posts:
                        self._debug_print(f"Skipping already seen post {post_id}")
                        continue

                    try:
                        # Check for "See more" button
                        see_more_button = story_div.find_elements(By.XPATH, './/div[@role="button" and text()="See more"]')
                        if see_more_button:
                            self._debug_print("Clicking 'See more' button.")
                            see_more_button[0].click()
                            time.sleep(1)  # Wait for content to load

                        text_elements = story_div.find_elements(By.XPATH, './/div')
                        final_text = text_elements[0].text if text_elements else ""

                        if final_text:
                            post_counter += 1
                            seen_posts.add(post_id)
                            found_new_post = True
                            
                            post_data = {
                                "post_number": post_counter,
                                "content": final_text,
                            }
                            print(f"Post {post_counter}/{max_posts}")
                            self._debug_print(f"Content preview: {final_text[:50]}...")

                            json_post = json.dumps(post_data, ensure_ascii=False, indent=2)
                            if not first_post:
                                file.write(",\n")
                            file.write(json_post)
                            file.flush()  # Flush the file buffer after each post
                            first_post = False

                        # Scroll to the next post
                        self._debug_print("Scrolling to next post...")
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", story_div)
                        time.sleep(2)  # Let the page render

                    except Exception as e:
                        self._debug_print(f"Error processing post: {str(e)}")
                        continue

                # If we didn't find any new posts in this iteration, we might be at the end
                if not found_new_post:
                    self._debug_print("No new posts found in this iteration. Attempting additional scrolls.")
                    for attempt in range(max_scroll_attempts):
                        self._debug_print(f"Additional scroll attempt {attempt + 1}/{max_scroll_attempts}")
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)  # Wait for potential new content to load
                        
                        # Check for new posts after scrolling
                        new_story_divs = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-ad-rendering-role="story_message"]')
                        if len(new_story_divs) > len(story_divs):
                            self._debug_print(f"Found {len(new_story_divs) - len(story_divs)} new posts after scrolling.")
                            found_new_post = True
                            break
                    
                    if not found_new_post:
                        self._debug_print("No new posts found after additional scrolling attempts. Stopping.")
                        break


            file.write("\n]")  # Close JSON array
            file.flush()  # Final flush

        print(f"Scraping completed. Output saved to {file_path}.")

    def close_browser(self):
        if self.debug:
            # Allows the user to manually check that all posts have been scraped before closing the browser
            input("Press Enter to close the browser...")
        
        self.driver.quit()


    def scrape(self):
        # Executes the Facebook group scraping process when the instance is called
        try:
            self.open_group_page()
            self.wait_for_user_login()
            self.scrape_posts()
        except Exception as e:
            print(f"An error occurred during scraping: {e}")
        finally:
            self.close_browser()
    
