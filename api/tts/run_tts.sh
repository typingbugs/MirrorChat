#!/bin/bash
FLASK_APP=main.py FLASK_ENV=development flask run \
    -h 0.0.0.0 \
    -p 9992