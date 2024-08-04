FROM tiangolo/uvicorn-gunicorn:python3.10

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY ./app/Room_Wall_Visualizer/requirements.txt /app/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt    

# https://stackoverflow.com/questions/47113029/importerror-libsm-so-6-cannot-open-shared-object-file-no-such-file-or-directo
RUN apt update && apt install -y ffmpeg libsm6 libxext6 

COPY ./app/Room_Wall_Visualizer /app