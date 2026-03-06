#!/bin/bash

echo "Starting backend..."
cd /app/backend
pip install -r requirements.txt
python server.py &

echo "Starting frontend..."
cd /app/frontend
yarn install
yarn start
