#!/bin/sh
while :; do
    source /home/johz/wfething-backend/bin/activate
    python server.py >> /home/johz/logs/wfeserver.log 2>&1
done