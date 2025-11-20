import matplotlib.pyplot as plt
from PIL import Image
import os

# Test paths
raw_img = r"D:\models\LLMs\hub\test_data\sample\digibok_2011041305069_0049.jpg"
portrait_img = r"D:\models\LLMs\hub\paddle_output\sample\digibok_2011041305069_0049\imgs\img_in_image_box_1397_1657_2035_2524.jpg"
output = r"V:\BDADShareData2\HCNC\norway\biographies\storage\paddleocr\test_display.png"

print(f"Raw image exists: {os.path.exists(raw_img)}")
print(f"Portrait exists: {os.path.exists(portrait_img)}")

# Create figure
fig, axes = plt.subplots(1, 2, figsize=(12, 6))

# Load and display raw image
if os.path.exists(raw_img):
    img1 = Image.open(raw_img)
    print(f"Raw image size: {img1.size}")
    axes[0].imshow(img1)
    axes[0].set_title("Raw Image")
    axes[0].axis('off')

# Load and display portrait
if os.path.exists(portrait_img):
    img2 = Image.open(portrait_img)
    print(f"Portrait size: {img2.size}")
    axes[1].imshow(img2)
    axes[1].set_title("Portrait")
    axes[1].axis('off')

plt.tight_layout()
plt.savefig(output, dpi=150, bbox_inches='tight')
print(f"\nSaved test image to: {output}")
