FROM python:3.9-slim-buster
WORKDIR /app
COPY ./requirements.txt /app

# Modify the example paths to pem files for setting up SSL 
COPY ${CERTIFICATE} /var/servercredentials/
COPY ${PRIVATE_KEY} /var/servercredentials/
ENV CERTIFICATE=/var/servercredentials/fullchain.pem
ENV PRIVATE_KEY=/var/servercredentials/privkey.pem

RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "./bot_line.py"]
