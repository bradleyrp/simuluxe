#!/bin/bash

#---automatically push current code to github

timestamp=$(date +%Y.%m.%d.%H%M)
du -h --max-depth=1
echo "pushing code to github via"
echo
echo "git commit -a -m \""$timestamp" : "${@:2}"\""
echo
read -p "confirmed? " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
	commit_message=$(echo $timestamp" : "${@:2})
	#git add . --all
  	#git commit -a -m \""$timestamp" : "${@:2}"\"
    #git push
    echo
    echo $commit_message
    echo 
fi
echo

