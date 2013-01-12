#!/bin/bash

while [[ 1 ]] ; do
	echo "Reboot Xiao Huangji" >> loop.log
	bash ./kill.sh
	sleep 2
	bash ./start.sh
	echo "Sleep 5min" >> loop.log
	sleep 300
done

exit 0 
