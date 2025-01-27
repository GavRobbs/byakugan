#!/bin/bash

cd stream_app

if [ -x "$(command -v python3)" ]; then
    PYTHON=$(command -v python3)
elif [ -x "$(command -v python)" ]; then
    PYTHON=$(command -v python)
else
    echo "Python is not installed on this system."
    exit 1
fi

echo "Setting up virtual environment and installing dependencies."
$PYTHON -m venv ./env || { echo "Failed to create virtual environment."; exit 1;}
source env/bin/activate || { echo "Failed to activate virtual environment."; exit 1;}
env/bin/python -m pip install -r requirements.txt || { echo "Failed to install dependencies"; exit 1;}
echo "Starting Byakugan's backend"
env/bin/python stream.py &

echo "Switching to the frontend folder."
cd ../byakugan-fe
echo "Installing NPM dependencies."
npm install

echo "Starting the app."
npm run dev &