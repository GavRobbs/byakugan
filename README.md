# Byakugan

## An Automated Video Surveillance System

Byakugan is an AVSS created in fulfilment of the requirements for the CM3070 Final Project. This repo contains two different programs:
- The frontend (byakugan-fe), which is a React application, built using Vite
- The backend (stream-app), which is a Python/Flask application

The program has been dockerized. To run it, you type **python deploy.py** and follow the instructions. When you're done with it, Ctrl+C to exit and run **python undeploy.py**. This is necessary for cleanup, especially on Windows, otherwise you may subsequently have issues restarting ffmpeg.

On Windows, you will need ffmpeg to get the camera working.