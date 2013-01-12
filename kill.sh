#!/bin/bash

ps aux | grep main.py | awk '{print $2}' | xargs kill
ps aux | grep rqworker | awk '{print $2}' | xargs kill

exit 0 

