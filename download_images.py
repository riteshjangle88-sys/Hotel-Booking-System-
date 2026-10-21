import os
import urllib.request

IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'static', 'images')

# Mapping of required image files to high-quality royalty-free Unsplash URLs
IMAGES = {
    'hero.jpg': 'https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=80',  # Taj Mahal Golden Hour
    'banner.jpg': 'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1200&q=80',  # Taj Mahal & Agra
    'hotel1.jpg': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80',   # Luxury Hotel Palace
    'hotel2.jpg': 'https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=800&q=80',   # Tropical Beach Resort (Goa)
    'hotel3.jpg': 'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=800&q=80',   # Mountain Travel Lodge
    'hotel4.jpg': 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=800&q=80',   # Classic Luxury Hotel
    'room1.jpg': 'https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=800&q=80',    # Standard Room
    'room2.jpg': 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80',    # Deluxe Room
    'room3.jpg': 'https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=800&q=80',    # Luxury Suite
    'logo.png': 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=200&q=80',    # Abstract Gold Pattern for Logo
}

def download_images():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    print(f"Ensured folder path: {IMAGE_DIR}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    for filename, url in IMAGES.items():
        filepath = os.path.join(IMAGE_DIR, filename)
        if os.path.exists(filepath):
            print(f"{filename} already exists, skipping.")
            continue
            
        print(f"Downloading {filename}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response, open(filepath, 'wb') as out_file:
                out_file.write(response.read())
            print(f"Successfully saved {filename}")
        except Exception as e:
            print(f"Error downloading {filename}: {e}")

if __name__ == '__main__':
    download_images()
