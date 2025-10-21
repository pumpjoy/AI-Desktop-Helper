# AI-Desktop-Helper
A local host AI that helps you do tasks such as
- Translate 12 languages
- Text summary
- Video summary (Youtube)

Future:
- Image and PDF translator

---------------
The app is coded with the help of 2.5 Flash, bug tested to ensure functionality.
Changes: 
- Build in model installer (predefined)

Future features will be added:
- Model related
    - Changing model
    - Automatically install pre-defined model (will not handle check PC spec)
- Youtube Video summary
    - Does not handle none Youtube/audio-to-text task (yet) <- could be hardware intensive, may need checkers before handling request to do so


Note: pdf-img.py is unrelated. An old project that can do things to pdf-img (merge, split, convert, etc)

---------------------------

# Use LM Studio to see if your pc can these models run!

# If using Ollama models
- It downloads the latest Ollama binary.
- It installs it to /usr/local/bin/ollama.
- It automatically creates and starts the ollama system service (systemd), 
- Ensuring Ollama runs silently in the background whenever your WSL instance is active.
`curl -fsSL https://ollama.com/install.sh | sh`

## Verify
`systemctl status ollama`

## Model 
`ollama run ibm/granite3.2:8b`    #Simple text summarizer - https://ollama.com/ibm/granite3.2:8b-instruct-q4_1
`ollama run mistral-small`        #Complicated text summarizer  -https://ollama.com/library/mistral-small