import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = "https://www.stonybrook.edu/commcms/studentaffairs/for/about/hours.php"
driver.get(url)

try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "tablesaw"))
    )
except:
    print("Page did not load properly.")
    driver.quit()
    exit()

soup = BeautifulSoup(driver.page_source, 'html.parser')
building_spans = soup.find_all('span', class_='red-header-style-h2')
all_data = []

for span in building_spans:
    building_name = span.get_text(strip=True)
    print(f"Scraping {building_name}...")

    next_table = span.find_parent('p').find_next_sibling('div').find_next_sibling('table')
    if next_table is None:
        continue  

    rows = next_table.find('tbody').find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 5:
            continue  
        
        day = cells[0].find('span', class_='red-header-style-h6').text.strip()
        fall = cells[1].find('strong').text.strip()
        winter = cells[2].find('strong').text.strip()
        spring = cells[3].find('strong').text.strip()
        summer = cells[4].find('strong').text.strip()

        from datetime import datetime

        def clean_time_range(time_range):
            if "Reservation" in time_range or "Closed" in time_range:
                return "Closed"
            
            # normalize dashes
            time_range = time_range.replace("–", "-").replace("—", "-")
            
            # split start and end
            parts = time_range.split("-")
            if len(parts) != 2:
                return "Closed"
            
            try:
                start = datetime.strptime(parts[0].strip().upper(), "%I:%M%p").strftime("%H:%M")
                end = datetime.strptime(parts[1].strip().upper(), "%I:%M%p").strftime("%H:%M")
                return f"{start},{end}"
            except:
                return "Closed"

        # Inside your row loop
        day_span = cells[0].find('span', class_='red-header-style-h6')
        day = day_span.text.strip() if day_span else cells[0].text.strip()
        fall = clean_time_range(cells[1].find('strong').text.strip())
        winter = clean_time_range(cells[2].find('strong').text.strip())
        spring = clean_time_range(cells[3].find('strong').text.strip())
        summer = clean_time_range(cells[4].find('strong').text.strip())

        all_data.append({
            'Building': building_name,
            'Day': day,
            'Fall': fall,
            'Winter': winter,
            'Spring': spring,
            'Summer': summer
        })


df = pd.DataFrame(all_data)
print(df)
df.to_csv('building_hours.csv', index=False)
driver.quit()
