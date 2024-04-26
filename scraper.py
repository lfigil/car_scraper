from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd
import time
import re

def save_to_csv(data_list, file_path):
    """Creates a new file if does not exists and appends a list"""

    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(data_list)
    
    # Check if the CSV file already exists
    file_exists = pd.io.common.file_exists(file_path)
    
    # If the file exists, append data without headers
    # Otherwise, write data with headers
    df.to_csv(file_path, mode='a', header=not file_exists, index=False)
    
    print(f"Saving {len(df)} listings...")

def extract_details(text):
    """Extracts mileage and accidents/owners/usage information from a given text string."""
    
    # Define regex pattern for mileage
    mileage_pattern = r'(\d{1,3}(?:,\d{3})*|\d+) miles'
    
    # Define regex pattern for accidents/owners/usage
    # Match the entire line(s) after mileage
    accidents_owners_usage_pattern = r'(?<=miles\n)(.*)'
    
    # Search for mileage
    mileage_match = re.search(mileage_pattern, text)
    if mileage_match:
        mileage = mileage_match.group(0)
    else:
        mileage = None
    
    # Search for accidents/owners/usage
    accidents_owners_usage_match = re.search(accidents_owners_usage_pattern, text, re.DOTALL)
    if accidents_owners_usage_match:
        accidents_owners_usage = accidents_owners_usage_match.group(1)
        accidents_owners_usage = accidents_owners_usage.split("\n")[0]
    else:
        accidents_owners_usage = None
    
    # Return the extracted information as a dictionary
    return {
        'mileage': mileage,
        'accidents_owners_usage': accidents_owners_usage
    }

def dict_maker(text):
    """accepts a string and returns a dictionary based on the contents of the string. 
    If a string line contains a semicolon (:), split the line into key and value, and add them to 
    the dictionary. If a string line does not contain a semicolon, generate a key like k1, k2, and so on, 
    and assign the line content as the value."""

    result_dict = {}
    lines = text.split("\n")

    for line in lines:
        line = line.strip()

        if line:
            if ":" in line:
                # Split by semicolon
                k, v = line.split(":", 1)

                k = k.strip()
                v = v.strip()

                # Add key value pair to dict
                result_dict[k] = v
    
    return result_dict


def page_scraper(driver):
    """Scrapes data from the current page and returns a list of dictionaries with items scraped."""
    vehicle_listings = []
    next_page = False
    next_page_url = ""

    try:
        # Find the list of listings
        unorder_list = driver.find_element(By.CSS_SELECTOR, "ul.usurp-card-list.list-unstyled.align-items-stretch.row")
        listings = unorder_list.find_elements(By.CSS_SELECTOR, "li.d-flex.mb-0_75.mb-md-1_5.col-12.col-md-6")
        
        # Loop through each listing
        for item in listings:
            try:
                # Extract vehicle information
                car_url = item.find_element(By.CSS_SELECTOR, 'a.usurp-inventory-card-vdp-link').get_attribute("href")
                y_m_m = item.find_element(By.CSS_SELECTOR, 'div.size-16.text-cool-gray-10.font-weight-bold.mb-0_5').text
                trim_style = item.find_element(By.CSS_SELECTOR, 'div.font-weight-normal.size-14.text-cool-gray-30').text
                price = item.find_element(By.CSS_SELECTOR, 'span.heading-3').text

                # Extract additional information as dictionary
                details = item.find_element(By.CSS_SELECTOR, 'div.text-gray-darker.row').text
                details_dict = extract_details(details)

                summary = item.find_element(By.CSS_SELECTOR, 'summary.px-0.py-0.small.text-primary-darker.d-flex.align-items-center.size-16.mt-1.justify-content-end')
                if not summary.is_selected():
                    summary.click()
                    time.sleep(0.5)  # Add a delay to allow content to load

                # Extract vehicle history and listing information
                try:
                    history = item.find_element(By.CSS_SELECTOR, 'section.srp-card-vehicle-history.mb-1').find_element(By.CSS_SELECTOR, 'div.row').text
                    history_dict = dict_maker(history)
                except NoSuchElementException:
                    history_dict = None
                
                try:
                    listing_info = item.find_element(By.CSS_SELECTOR, 'details.view-more').find_elements(By.CSS_SELECTOR, 'p.xsmall.mb-1')[-1].text
                    listing_info_dict = dict_maker(listing_info)
                except NoSuchElementException:
                    listing_info = None

                # Create a dictionary with vehicle information
                vehicle_dict = {
                    'year_make_model': y_m_m,
                    'trim_style': trim_style,
                    'price': price,
                    'url': car_url
                }

                # Update vehicle_dict with additional details, history, and listing information
                vehicle_dict.update(details_dict)
                
                if history_dict:
                    vehicle_dict.update(history_dict)
                
                if vehicle_dict:
                    vehicle_dict.update(listing_info_dict)

                # Add the vehicle_dict to vehicle_listings
                vehicle_listings.append(vehicle_dict)

            except (NoSuchElementException, StaleElementReferenceException) as e:
                print(f"Skipping listing due to: {e}")
                continue
            except Exception as e:
                print(f"Unhandled error processing listing: {e}")
                continue

        # Find and handle the "Next" button for pagination
        next_buttons = driver.find_elements(By.CSS_SELECTOR, 'a.pagination-btn.rounded.d-flex.align-items-center.justify-content-center.text-blue-30.mx-1_5')
        
        if len(next_buttons) > 1:  # Ensure there is more than one button available
            next_button = next_buttons[1]  # Assuming the second button is the "Next" button

            if next_button.get_attribute("aria-disabled") == 'true':
                next_page = False
                next_page_url = ""
            else:
                next_page = True
                next_page_url = next_button.get_attribute("href")
            
                print(f"NEXT PAGE: {next_page_url}")

        return vehicle_listings, next_page, next_page_url

    except Exception as e:
        print(f"Error in scraper: {e}")
        return vehicle_listings, False, ""


# Define a function to initialize a new WebDriver session
def initialize_webdriver(url):
    # Set up Selenium options
    options = Options()
    options.add_argument('--incognito')
    
    # Create a new WebDriver instance
    driver = webdriver.Chrome(options=options)
    
    # driver.minimize_window()
    # Load the URL
    driver.get(url)
    driver.implicitly_wait(5)
    
    return driver

# Define a function to close the WebDriver instance
def close_webdriver(driver):
    # Close the WebDriver instance
    if driver:
        driver.quit()

def save_last_url(url, file_path='last_url.txt'):
    with open(file_path, 'w') as f:
        f.write(url)

# Define the main function to perform the scraping and navigation
def main():
    # sedan_url = "https://www.edmunds.com/inventory/srp.html?inventorytype=used%2Ccpo&make=honda%2Ctoyota%2Cmazda&model=honda%7Ccivic%2Ctoyota%7Ccorolla%2Ctoyota%7Ccamry%2Cmazda%7C3%2Cmazda%7C6&pagenumber=100&radius=25&year=2021-*"
    suv_url = "https://www.edmunds.com/inventory/srp.html?inventorytype=used%2Ccpo&make=toyota%2Chonda%2Cmazda&model=toyota%7Crav4%2Chonda%7Ccr-v%2Chonda%7Cpilot%2Cmazda%7Ccx-5&pagenumber=183&radius=25&year=2021-*"
    default_path = suv_url
    save_file_path = 'vehicle_data/suv_vehicles.csv'
    
    # Initialize the WebDriver
    driver = initialize_webdriver(default_path)
    
    while True:
        # Scrape the page and navigate to the next page
        vehicles_list, next_page, new_url = page_scraper(driver)
        
        # Save the scraped data to CSV
        # save_to_csv(vehicles_list, save_file_path)

        save_last_url(new_url)
        
        # Check if there is a next page to navigate to
        if next_page:
            # Close the current WebDriver instance
            close_webdriver(driver)
            
            # Initialize a new WebDriver instance with the updated URL
            driver = initialize_webdriver(new_url)
            
            # Add a delay between page navigations
            time.sleep(0.5)
        else:
            # No more pages to navigate to, break the loop
            break
        break
    
    # Close the WebDriver when done
    close_webdriver(driver)

if __name__ == "__main__":
    main()