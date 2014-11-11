#!/bin/bash

#---automatically push current code to github

timestamp=$(date +%Y.%m.%d.%H%M)
du -h --max-depth=1
echo "pushing code to github via"
echo
echo "git commit -a -m \""$timestamp" : "${@:2}"\""
echo
read -p "okay to commit and push y/N? " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
	echo "HEY"
	commit_message=$timestamp" : "${@:2}
	git add . --all
  	git commit -a -m "$commit_message"
    git push
fi
echo

