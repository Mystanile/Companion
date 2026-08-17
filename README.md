# Companion

An AI-powered voice-controlled desktop assistant for Windows that understands natural language commands and helps you manage files, open applications, and more.

## Features

- **🎤 Voice Interface**: Talk to your desktop assistant using your microphone
  - Speech-to-text powered by Whisper (large-v3-turbo)
  - Advanced LLM processing with Llama 3.3 70B
  - Natural text-to-speech responses via Edge TTS

- **⌨️ Hotkey Activation**: Press backtick (`` ` ``) to talk, release to send
  - Simple and intuitive activation
  - Customizable hotkey in config

- **🎯 Visual Feedback**: Beautiful overlay orb in the corner of your screen
  - Shows current state (idle, listening, thinking, speaking)
  - System tray integration
  - Non-intrusive UI

- **🛠️ Desktop Tools**: The assistant can:
  - Open files and folders
  - Open URLs and links
  - Create, edit, and manage files
  - List directory contents
  - Move, copy, rename, and delete files

- **⚙️ Configurable**: Customize via simple YAML config
  - Adjust hotkey, overlay position and size
  - Configure voice models and voices
  - Set file system access boundaries

## Requirements

- Windows 10 or later
- Python 3.10+
- Groq API key (get one free at [console.groq.com](https://console.groq.com))
- Microphone for voice input
- Speakers or headphones for audio output

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/companion.git
   cd companion
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Groq API key**:
   - Create a `.env` file in the project root
   - Add your Groq API key:
     ```
     GROQ_API_KEY=your_api_key_here
     ```

4. **Run the application**:
   ```bash
   python main.py
   ```

## Configuration

Edit `config.yaml` to customize Companion:

```yaml
# Activation hotkey (default: backtick)
hotkey: "`"

# Overlay display settings
overlay:
  size: 72                # Orb size in pixels
  orb_size: 56           # Inner orb size
  left_margin: 28        # Distance from left edge
  bottom_margin: 28      # Distance from bottom edge

# Voice and AI models
voice:
  stt_model: whisper-large-v3-turbo  # Speech-to-text model
  llm_model: llama-3.3-70b-versatile # Language model
  tts_voice: en-US-AriaNeural        # Text-to-speech voice

# File system access boundaries
paths:
  allowed_roots:
    - "~"                # Allow access to home directory
```

## How to Use

1. Launch the application: `python main.py`
2. You'll see a small orb appear in the bottom-left corner of your screen
3. Press and hold the backtick key (`` ` ``) to start recording
4. Speak your command naturally (e.g., "Open my Documents", "Create a new file called todo.txt")
5. Release the key when done speaking
6. The assistant will process your request and respond with voice feedback

## Examples

Try these commands:

- "Open my downloads folder"
- "Create a new file called notes.txt in my documents"
- "Open google.com in my browser"
- "Delete that old file on my desktop"
- "What time is it?"
- "Open this file with VS Code"

## Project Structure

```
companion/
├── agent.py       # AI agent logic and tool execution
├── app_paths.py   # Application path resolution
├── overlay.py     # Visual overlay UI
├── paths.py       # Path validation and security
├── tools.py       # Available tools for the assistant
├── voice.py       # Voice recording and synthesis
└── __init__.py

main.py            # Application entry point
config.yaml        # Configuration file
requirements.txt   # Python dependencies
```

## Security

- The assistant can only access files under the configured allowed roots (by default, your home directory)
- All paths are validated before access
- The agent is designed to ask for clarification on ambiguous requests
- Be careful with delete commands - they require explicit user confirmation in speech

## Dependencies

- **groq**: LLM API access
- **PyQt6**: Desktop GUI and system tray
- **edge-tts**: Text-to-speech synthesis
- **sounddevice**: Audio recording
- **keyboard**: Global hotkey detection
- **pyyaml**: Configuration parsing

See `requirements.txt` for full list.

## Troubleshooting

**"Missing GROQ_API_KEY" error**
- Ensure your `.env` file exists and contains your Groq API key
- The file should be in the project root directory

**No sound output**
- Check your speaker/headphone connections
- Verify volume levels in Windows audio settings
- Try a different TTS voice in config.yaml

**Hotkey not working**
- Some applications may capture the global hotkey
- Try a different hotkey in config.yaml
- Ensure the application has permission to capture keyboard input

## License

MIT License - feel free to use, modify, and distribute

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Future Improvements

- Support for additional languages
- Windows 11 chat widget integration
- Plugin system for custom tools
- System command automation
- Integration with external APIs
- Custom voice model support
