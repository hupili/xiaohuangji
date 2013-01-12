#!/bin/bash

ps aux | grep main.py | grep -v grep
ps aux | grep rqworker | grep -v grep 

exit 0 
