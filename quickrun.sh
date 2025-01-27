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
$PYTHON -m venv env
source env/bin/activate
$PYTHON -m pip install -r requirements.txt
echo "Starting Byakugan's backend"
$PYTHON stream.py &

cd ../byakugan-fe
npm run dev