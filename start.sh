#!/bin/bash

nohup sh -c 'python -u main.py 2>&1 | tee -a main.log' &
nohup sh -c 'rqworker 2>&1 | tee -a worker.log' &

exit 0 
