
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from urllib.parse import quote

class CarScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def search_cars(self, search_term, num_pages=1):
        # Encode search term for URL
        encoded_search = quote(search_term)
        base_url = f"https://www.ouedkniss.com/recherche?query={encoded_search}&category=automobiles_vehicules"
        return self.scrape_listings_page(base_url, num_pages)

    def scrape_listings_page(self, url, num_pages=1):
        all_cars = []
        current_page = 1
        
        try:
            while current_page <= num_pages:
                self.driver.get(url)
                time.sleep(5)
                
                # Wait for the content to load
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "v-card")))
                
                # Get all car cards
                cards = self.driver.find_elements(By.CLASS_NAME, "o-announ-card")
                
                for card in cards:
                    try:
                        car_details = self._extract_card_details(card)
                        if car_details:
                            all_cars.append(car_details)
                    except Exception as e:
                        continue
                
                # Handle pagination
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, "[aria-label='Next page']")
                    if not next_button.is_enabled():
                        break
                    next_button.click()
                    time.sleep(3)
                except:
                    break
                
                current_page += 1
                
            return all_cars
            
        except Exception as e:
            return all_cars

    def _extract_card_details(self, card):
        try:
            # Extract image URL
            try:
                img_element = WebDriverWait(card, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img.ok-img"))
                )
                image_url = img_element.get_attribute('src')
            except:
                image_url = None

            # Extract title
            try:
                title_element = WebDriverWait(card, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "o-announ-card-title"))
                )
                title = title_element.text.strip()
            except:
                title = None

            # Extract price
            try:
                price = card.find_element(By.CLASS_NAME, "price").text.strip()
            except:
                price = "Prix non spécifié"

            # Extract specifications
            try:
                specs = [spec.text.strip() for spec in card.find_elements(By.CLASS_NAME, "v-chip")]
            except:
                specs = []

            # Extract location
            try:
                location_icon = card.find_element(By.CLASS_NAME, "mdi-map-marker")
                location = location_icon.find_element(By.XPATH, "./following-sibling::span").text.strip()
            except:
                location = None

            # Extract posted time
            try:
                time_icon = card.find_element(By.CLASS_NAME, "mdi-update")
                posted_time = time_icon.find_element(By.XPATH, "./following-sibling::span").text.strip()
            except:
                posted_time = None

            # Extract listing URL
            try:
                listing_url = card.find_element(By.CSS_SELECTOR, "a[href*='voitures-']").get_attribute('href')
            except:
                listing_url = None

            return {
                'title': title,
                'price': price,
                'specifications': specs,
                'location': location,
                'posted_time': posted_time,
                'image_url': image_url,
                'listing_url': listing_url
            }
        except Exception as e:
            return None

    def close(self):
        self.driver.quit()

def main():
    st.set_page_config(page_title="Car Listings Scraper", layout="wide")
    
    # Add CSS for better card layout
    st.markdown("""
    <style>
    .car-card {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin-bottom: 20px;
    }
    .car-image {
        width: 100%;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Title and description
    st.title("🚗 Car Listings Scraper")
    st.markdown("Search for car listings on Ouedkniss")
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Enter search term (e.g., 'Golf 7' or 'BMW')")
    with col2:
        num_pages = st.number_input("Number of pages to scrape", min_value=1, max_value=5, value=1)
    
    # Search button
    if st.button("Search"):
        if search_term:
            # Initialize progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Create scraper instance
            scraper = CarScraper()
            try:
                # Update status
                status_text.text("Searching for listings...")
                
                # Perform search
                results = scraper.search_cars(search_term, num_pages)
                
                if results:
                    st.success(f"Found {len(results)} listings!")
                    
                    # Display results in a grid
                    cols = st.columns(3)
                    for idx, car in enumerate(results):
                        with cols[idx % 3]:
                            st.markdown(f"""
                            <div class="car-card">
                                <h3>{car['title']}</h3>
                                <img src="{car['image_url']}" class="car-image" onerror="this.src='https://via.placeholder.com/300x200'">
                                <p><strong>Price:</strong> {car['price']}</p>
                                <p><strong>Location:</strong> {car['location']}</p>
                                <p><strong>Posted:</strong> {car['posted_time']}</p>
                                <p><strong>Specs:</strong> {', '.join(car['specifications'])}</p>
                                <a href="{car['listing_url']}" target="_blank">View Listing</a>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("No results found.")
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
            
            finally:
                scraper.close()
                progress_bar.progress(100)
                status_text.text("Search completed!")
        else:
            st.warning("Please enter a search term.")

if __name__ == "__main__":
    main()