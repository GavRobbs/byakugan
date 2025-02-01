#I was advised to use a multistage build for this, first to build the node app
#Then the second stage to deploy via nginx

#Stage 1: The nodeJs stage
FROM node:22 AS builder
WORKDIR /app

#Install vite/react dependecies
COPY package.json package-lock.json ./
RUN npm install

#Build the vite/react app
COPY . .
RUN npm run build

#Stage 2: The nginx serve stage

FROM nginx:latest

RUN rm -f /etc/nginx/conf.d/default.conf
WORKDIR /usr/share/nginx/html

#clear the default nginx html files and copy the build from the first stage
RUN rm -rf ./*
COPY --from=builder /app/dist ./
COPY --from=builder /app/nginx.conf /etc/nginx/conf.d/default.conf 

#run nginx in foreground mode otherwise it won't work
CMD ["nginx", "-g", "daemon off;"]

#this is just metadata to say we're exposing port 80
EXPOSE 80
