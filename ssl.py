import numpy as np
import matplotlib.pyplot as plt
from sklearn.neural_network import MLPRegressor
from PIL import Image

# 1️⃣ Load and prepare the image
img = Image.open("cat.jpg").convert("L")  # convert to grayscale

# show the picture
plt.imshow(img)
plt.title("Original Image")
plt.axis("off")
plt.show()

img = img.resize((64, 64))  # resize to smaller image for faster processing
image = np.array(img) / 255.0  # convert to NumPy array and normalize (0–1)

# 2️⃣ Mask (hide) random pixels (simulate missing data)
mask = np.random.rand(*image.shape) > 0.7  # same shape as image
masked_image = image.copy()
masked_image[mask] = 0  # hide masked pixels

plt.title("Masked Image (Input)")
plt.imshow(masked_image, cmap='gray')
plt.axis("off")
plt.show()

# 3️⃣ Prepare training data
X = []
y = []

height, width = image.shape
for i in range(height):
    for j in range(width):
        if mask[i, j]:  # only train on masked pixels
            # Extract 3x3 patch around the pixel (with padding at edges)
            top, bottom = max(i - 1, 0), min(i + 2, height)
            left, right = max(j - 1, 0), min(j + 2, width)
            patch = masked_image[top:bottom, left:right]

            # Pad patch to always be 3x3
            padded = np.zeros((3, 3))
            padded[:patch.shape[0], :patch.shape[1]] = patch

            X.append(padded.flatten())
            y.append(image[i, j])  # true pixel value

X = np.array(X)
y = np.array(y)

print(f"Training samples: {len(X)}")

# 4️⃣ Train a small neural network to predict missing pixels
model = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=300, random_state=42)
model.fit(X, y)

# 5️⃣ Reconstruct the masked image
reconstructed = masked_image.copy()
for i in range(height):
    for j in range(width):
        if mask[i, j]:
            top, bottom = max(i - 1, 0), min(i + 2, height)
            left, right = max(j - 1, 0), min(j + 2, width)
            patch = masked_image[top:bottom, left:right]

            # Pad patch to 3x3
            padded = np.zeros((3, 3))
            padded[:patch.shape[0], :patch.shape[1]] = patch

            reconstructed[i, j] = model.predict([padded.flatten()])[0]

# 6️⃣ Display results
plt.figure(figsize=(10, 4))
plt.subplot(1, 3, 1)
plt.title("Original")
plt.imshow(image, cmap='gray')
plt.axis("off")

plt.subplot(1, 3, 2)
plt.title("Masked")
plt.imshow(masked_image, cmap='gray')
plt.axis("off")

plt.subplot(1, 3, 3)
plt.title("Reconstructed")
plt.imshow(reconstructed, cmap='gray')
plt.axis("off")

plt.show()
