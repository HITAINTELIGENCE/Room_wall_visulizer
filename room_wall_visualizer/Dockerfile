FROM tiangolo/uvicorn-gunicorn:python3.10

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY ./app/Room_Wall_Visualizer/requirements.txt /app/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt    

COPY ./app/Room_Wall_Visualizer /app

# Expose the port that the FastAPI app runs on
EXPOSE 8080

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]