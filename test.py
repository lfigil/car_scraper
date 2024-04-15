from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd
import time

def save_to_csv(data_list, file_path):
    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(data_list)
    
    # Append the DataFrame to the CSV file. Specify 'a' mode to append and 'header' as False to not include header again.
    df.to_csv(file_path, mode='a', header=False, index=False)

    print(f"Saving {len(df)} listings...")

default_path = "https://www.edmunds.com/inventory/srp.html?inventorytype=used%2Ccpo&radius=25&make=honda&model=honda%7Ccr-v"
file_path = '/home/lfigil/Documents/car_scraper/honda_data2.csv'

while True:
    vehicles_list = []
    # Set up Selenium options
    options = Options()
    options.add_argument('--incognito')
    # options.add_argument('--headless')

    driver = webdriver.Chrome(options=options)

    # Load the URL
    driver.get(default_path)
    driver.implicitly_wait(2)
    
    try:
        # Locate the list of vehicle listings on the current page
        unorder_list = driver.find_element(By.CSS_SELECTOR, "ul.usurp-card-list.list-unstyled.align-items-stretch.row")
        listings = unorder_list.find_elements(By.CSS_SELECTOR, "li.d-flex.mb-0_75.mb-md-1_5.col-12.col-md-6")

        # Scrape data for each listing
        for listing in listings:
            try:
                # Scrape the data
                car_url = listing.find_element(By.CSS_SELECTOR, 'a').get_attribute("href")
                car_year_model = listing.find_element(By.CSS_SELECTOR, 'div.left-section.py-0.pl-0.pr-0_5.col-7').text
                car_price = listing.find_element(By.CSS_SELECTOR, 'div.pr-0.text-right.d-flex.justify-content-between.col-5').text
                car_details = listing.find_element(By.CSS_SELECTOR, 'div.text-gray-darker.row').text

                # Open the <details> tag to scrape additional information
                summary = listing.find_element(By.CSS_SELECTOR, 'summary')
                if not summary.is_selected():
                    summary.click()  # Open the <details> tag
                    time.sleep(1)  # Add a delay to allow the content to load

                # Scrape the long details
                details_2 = listing.find_elements(By.TAG_NAME, 'p')
                car_details_long = [d.text for d in details_2]

                # Store the vehicle data in a dictionary
                vehicle = {
                    'url': car_url,
                    'year_model': car_year_model,
                    'price': car_price,
                    'details_short': car_details,
                    'details_long': car_details_long
                }

                # Append the vehicle data to the list
                vehicles_list.append(vehicle)

            except NoSuchElementException as e:
                # print(f"Error processing listing: {e}")
                continue
            except StaleElementReferenceException:
                # Skip the listing if it's no longer valid
                continue
            except Exception as e:
                print(f"Unhandled error processing listing: {e}")
                continue
        
        save_to_csv(vehicles_list, file_path)

        # Locate the "Next" button and click it to navigate to the next page
        next_button = driver.find_elements(By.CSS_SELECTOR, 'a.pagination-btn.rounded.d-flex.align-items-center.justify-content-center.text-blue-30.mx-1_5')[1]
        
        # Check if the "Next" button is disabled
        if next_button.get_attribute("aria-disabled") == 'true':
            break
                
        # Click the "Next" button to navigate to the next page
        default_path = next_button.get_attribute("href")
        print(f"new path: {default_path}")
        
        driver.quit()
    except Exception as e:
        print(f"Error loading page: {e}")
        break
    finally:
        # Ensure the WebDriver is closed properly
        driver.quit()

driver.quit()