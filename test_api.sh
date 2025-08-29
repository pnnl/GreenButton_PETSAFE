#!/bin/bash

# Run the API in test mode (no database setup needed)

cd api
python wsgi.py --test