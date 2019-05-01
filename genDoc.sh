#!/bin/sh

PROJECT_TEMP_FOLDER=WirelessModularTestbed
mkdir $PROJECT_TEMP_FOLDER
mv ./* ./$PROJECT_TEMP_FOLDER
make -C ./$PROJECT_TEMP_FOLDER/docs/ html
mv ./$PROJECT_TEMP_FOLDER/docs/_build/html ./
rm -r ./$PROJECT_TEMP_FOLDER

git checkout gh-pages
mkdir git_temp
mv ./* ./git_temp
mv ./git_temp/html ./
rm -r ./git_temp
mv ./html/* ./
rm -r html
