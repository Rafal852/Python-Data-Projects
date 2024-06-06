import requests
from bs4 import BeautifulSoup
import csv
import time

base_url = 'https://www.olx.pl'
start_url = f'{base_url}/nieruchomosci/mieszkania/wynajem/wroclaw/'

def get_soup(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        print(f'Failed to retrieve {url}')
        return None

def extract_listing_data(listing):
    title = listing.find('h6').text if listing.find('h6') else 'Brak tytułu'
    price = listing.find('p', {'data-testid': 'ad-price'}).text if listing.find('p', {'data-testid': 'ad-price'}) else 'Brak ceny'
    location_date = listing.find('p', {'data-testid': 'location-date'}).text if listing.find('p', {'data-testid': 'location-date'}) else 'Brak lokalizacji'
    location = location_date.split(',')[0] if ',' in location_date else location_date

    anchor_tag = listing.find('a')
    if anchor_tag:
        href = anchor_tag.get('href', '')
        if href.startswith('http://') or href.startswith('https://'):
            url = href
        else:
            url = base_url + href

        # Extract details from the detailed page only if URL is valid
        details = get_detailed_listing_data(url)
    else:
        return None

    return {'title': title, 'price': price, 'location': location, **details}

def get_detailed_listing_data(url):
    soup = get_soup(url)
    if not soup:
        return {'rent': 'Brak rentu', 'furnishings': 'Brak umeblowania', 'floor': 'Brak piętra', 'room_number': 'Brak liczby pokoi', 'area': 'Brak powierzchni'}

    # Extract "rent"
    rent_tag = soup.find('p', text=lambda x: x and 'rent' in x.lower())
    rent = rent_tag.text.strip() if rent_tag else 'Brak czynszu'

    # Extract "umeblowanie" (furnishings)
    furnishings_tag = soup.find('p', text=lambda x: x and 'umeblowanie' in x.lower())
    furnishings = furnishings_tag.text.strip() if furnishings_tag else 'Brak umeblowania'

    # Extract "piętro" (floor)
    floor_tag = soup.find('p', text=lambda x: x and 'piętro' in x.lower())
    floor = floor_tag.text.strip() if floor_tag else 'Brak piętra'

    # Extract room number
    room_number_tag = soup.find('p', text=lambda x: x and 'pokoi' in x.lower())
    room_number = room_number_tag.text.strip() if room_number_tag else 'Brak liczby pokoi'

    # Extract area
    area_tag = soup.find('p', text=lambda x: x and 'powierzchnia' in x.lower())
    area = area_tag.text.strip() if area_tag else 'Brak powierzchni'

    return {
        'rent': rent,
        'furnishings': furnishings,
        'floor': floor,
        'room_number': room_number,
        'area': area
    }

# Find the listings and extract the data
def scrape_listings(url):
    soup = get_soup(url)
    if not soup:
        return []

    listings = soup.find_all('div', class_='css-1sw7q4x')
    data = []
    for listing in listings:
        listing_data = extract_listing_data(listing)
        if listing_data:
            data.append(listing_data)

    # Check for next page link
    next_page = soup.find('a', {'data-testid': 'pagination-forward'})
    if next_page:
        next_url = base_url + next_page['href']
        time.sleep(1)  # Be kind to the server
        data.extend(scrape_listings(next_url))

    return data

# Main scraping function
listings_data = scrape_listings(start_url)

# Print listings data
print("Listings Data:", listings_data)

# Save data to CSV
csv_file = 'listings.csv'
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    fieldnames = ['title', 'price', 'location', 'rent', 'furnishings', 'floor', 'room_number', 'area']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for listing in listings_data:
        writer.writerow(listing)

print(f'Data has been saved to {csv_file}')

