#This is a multistep build
#Stage 1: The nodeJs stage
FROM node:22 AS builder
WORKDIR /app

#Install vite/react dependecies
COPY ./byakugan-fe/package.json ./byakugan-fe/package-lock.json ./
RUN npm install

#Build the vite/react app
COPY ./byakugan-fe ./
RUN npm run build

#Stage 2
FROM python:3.12
WORKDIR /usr/src/app

#Install ffmpeg and sqlite3
RUN apt-get update && apt-get install -y ffmpeg && apt-get install -y sqlite3

COPY ./stream_app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./stream_app/* ./
COPY --from=builder /app/dist ../frontend/

CMD ["python", "./stream.py"]

EXPOSE 5000
