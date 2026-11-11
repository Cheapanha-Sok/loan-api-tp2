# Development image for the loan API (Lesson 4.3)
# 1. Start from a slim Python base
FROM python:3.12-slim

# 2. Work inside /app
WORKDIR /app

# 3. Copy only the dependency list first, so this layer stays cached
COPY requirements.txt .

# 4. Install the pinned packages
RUN pip install --no-cache-dir -r requirements.txt

# 5. Train the model inside the image, with the image's own scikit-learn
COPY train.py .
RUN python train.py

# 6. Document the port the API listens on
EXPOSE 8000

# 7. Copy the application code last (changes most often)
COPY . .

# Start the production server (listens on 0.0.0.0)
CMD ["fastapi", "run", "main.py", "--port", "8000"]
