#!/bin/sh
/usr/local/lib/python3.9/site-packages/gunicorn --chdir app application:application -w 2 --threads 2 -b 0.0.0.0:5000