#!/bin/sh

python3.10 Python-src/TGBot.py &
disown

echo "Теперь Python-скрипт будет работать до тех пор, пока не произойдёт перезагрузка, либо же ты не используешь команду 'pkill python'."
