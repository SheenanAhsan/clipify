### to run locally, you need to run python in a virtual machine


# run for first time
```
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install openai-whisper torch moviepy ffmpeg-python
```

### check if whisper is working
`python -m whisper --help`

### every other time
```
python3 -m venv venv
source venv/bin/activate
```

### run app
`python3 app.py`

### deactivate virtual environment
`deactivate`