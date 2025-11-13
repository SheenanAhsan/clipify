### to run locally, you need to run python in a virtual machine

# run for first time
```
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install faster-whisper ffmpeg-python srt
```

### every other time
`source venv/bin/activate`

### run app
`python3 app.py`

### deactivate virtual environment
`deactivate`