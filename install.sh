#!/usr/bin/env bash

PATH_PROJECT="$PWD"
echo "$PATH_PROJECT"
python3 -m venv "$PATH_PROJECT/venv"
source "$PATH_PROJECT/venv/bin/activate"
pip install pyTelegramBotAPI
deactivate