FROM public.ecr.aws/lambda/python:3.11

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy all files in ./src
COPY src/* ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler.
CMD [ "main.handler" ]

# Build dockerfile
# docker build -t docker-image:test .
# Run image
# docker run -p 9000:8080 docker-image:test
# curl "http://localhost:9000" -d ‘{}’