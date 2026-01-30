import requests
from PIL import Image, ImageDraw, ImageFont
import io

# 1. Create a dummy image with text
img = Image.new('RGB', (200, 100), color = (255, 255, 255))
d = ImageDraw.Draw(img)
d.text((10,10), "Hello World Test", fill=(0,0,0))

# Save to byte buffer
img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='PNG')
img_byte_arr.seek(0)

# 2. Upload to API
url = "http://127.0.0.1:8000/upload_pdfs/"
files = {'files': ('test_image.png', img_byte_arr, 'image/png')}

try:
    print(f"📡 Sending POST request to {url}...")
    response = requests.post(url, files=files)
    
    print(f"CODE: {response.status_code}")
    print(f"RESPONSE: {response.text}")
    
    if response.status_code == 200:
        print("✅ SUCCESS: Backend is working and accepting uploads.")
    else:
        print("❌ FAIL: Backend returned error.")

except Exception as e:
    print(f"❌ CONNECTION ERROR: {e}")
