# Byakugan

## An Automated Video Surveillance System

Byakugan is an AVSS created in fulfilment of the requirements for the CM3070 Final Project. This repo contains two different programs:
- The frontend (byakugan-fe), which is a React application, built using Vite
- The backend (stream-app), which is a Python/Flask application

The bare minimum dependencies are npm and python3.

The backend uses SQLite as the data store, so no database configuration is necessary. The script to run is stream.py, but do not run it using Flask, instead run it as a regular module with **python stream.py**. 

The frontend you will have to build with **npm run build**, then move the dist folder to wherever you serve HTML from on your server.

The first time you serve the frontend app, you may have to go to the settings and set the IP address of the backend server. If you're running it on the same computer, it should be 127.0.0.1 and work out of the box, but if you're running the server on another computer, you'll have to enter the address yourself.