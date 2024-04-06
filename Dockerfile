# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the Python script into the container
COPY fairyring_cli.py ./

# Install any necessary dependencies
RUN pip install websockets requests python-dotenv

# Define the entrypoint to run the script
ENTRYPOINT ["python", "fairyring_cli.py"]
