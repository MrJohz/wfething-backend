#! /bin/sh
source bin/activate
nohup python server.py >> serverlogs.log &
echo "Last PID:" $!
echo $! > PIDFILE.pid
