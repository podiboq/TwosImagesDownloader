import re
import sys
import os
import requests
import hashlib
from PIL import Image
from io import BytesIO

# Check if the user provided the required parameters
if len(sys.argv) < 2:
    print("Usage: python twosImageExtractor.py <input_markdown_file> [--optimize]")
    sys.exit(1)

input_file = sys.argv[1]
# Should we optimize the images?
optimize_images = "--optimize" in sys.argv
# At the end I want to create a copy of the input file with links to the downloaded images
output_file = os.path.splitext(input_file)[0] + "_local_images.md"

# Define the regex pattern for getting only the image links 
pattern = re.compile(r'https?://[^\s]+amazonaws[^\s]+?\.(?:jpg|jpeg|heic|png)\S*', re.IGNORECASE)

# Read the input markdown file
with open(input_file, "r", encoding="utf-8") as file:
    content = file.read()

# Find all matching links
links = pattern.findall(content)

# Write all the links to the links.txt file (I don't know if this part is really important, but hey... maybe I'll need them one day)
with open("links.txt", "w", encoding="utf-8") as file:
    file.write("\n".join(links))

# Create the /images folder if not exists
images_dir = "images"
os.makedirs(images_dir, exist_ok=True)

# Download, optionally optimize, and replace links
for index, link in enumerate(links, start=1):
    try:
        response = requests.get(link, stream=True)
        if response.status_code == 200:
            file_ext = re.search(r'(\.jpg|\.jpeg|\.heic|\.png)', link, re.IGNORECASE)
            if file_ext:
                file_ext = file_ext.group(1).lower()
            else:
                file_ext = ".jpg"  # Default extension if not found
            
            # Generate my own unique 25-character hash filename (to avoid issues with the original AWS names)
            hash_name = hashlib.sha256(link.encode()).hexdigest()[:25] + file_ext
            filepath = os.path.join(images_dir, hash_name)
            
            if optimize_images:
                # Open and resize the image
                image = Image.open(BytesIO(response.content))
                image.thumbnail((1024, 1024))  # Resize while maintaining aspect ratio
                image.save(filepath, optimize=True, quality=85)  # Optimize and reduce quality
                print(f"Downloaded, optimized, and replaced file {index} of {len(links)}: {hash_name}")
            else:
                # If the optimize process hasn't been requested, let's just save the image as it is
                with open(filepath, "wb") as img_file:
                    for chunk in response.iter_content(1024):
                        img_file.write(chunk)
                print(f"Downloaded and replaced file {index} of {len(links)}: {hash_name}")
            
            # Replace original image link with the path to the downloaded file
            content = content.replace(link, f"images/{hash_name}")
    except Exception as e:
        print(f"Failed to download {link}: {e}")

# Save the updated markdown file
with open(output_file, "w", encoding="utf-8") as file:
    file.write(content)

# Print the total number of links found (just for fun, as we already know this info by now :D)
print(f"Total links found: {len(links)}")
