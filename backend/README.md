# Voice AI Agent Backend

> 🎙️ **AI Voice Agents Challenge by murf.ai**
>
> This backend uses **Murf Falcon TTS** for ultra-fast voice synthesis, **Google Gemini** as the LLM, and **Cartesia Ink-Whisper** for STT.
> See the [main README](../README.md) for complete setup instructions and challenge details.

A voice AI assistant built with [LiveKit Agents for Python](https://github.com/livekit/agents) integrated with Murf Falcon TTS.

## Project Structure

```
backend/
├── src/
│   └── agent.py          # Main agent implementation
├── tests/                # Test suite
├── orders/               # Order data storage (JSON files)
├── shared-data/          # Shared data files
│   ├── orders.json
│   └── active_lead.json
├── KMS/                  # Knowledge Management System
│   └── logs/
├── AGENTS.md             # Guide for AI assistants working on this codebase
├── Dockerfile            # Production deployment
├── pyproject.toml        # Python dependencies (uv package manager)
├── taskfile.yaml         # Task automation
└── .env.local            # Environment configuration
```

## Tech Stack

| Component | Provider | Model |
|-----------|----------|-------|
| **STT** (Speech-to-Text) | Cartesia | `ink-whisper` |
| **LLM** (Large Language Model) | Google | `gemini-2.5-flash` |
| **TTS** (Text-to-Speech) | Murf Falcon | `en-US-matthew` (Conversation style) |
| **VAD** (Voice Activity Detection) | Silero | Default |
| **Turn Detection** | LiveKit | Multilingual Model |
| **Noise Cancellation** | LiveKit | BVC (Background Voice Cancellation) |

## Features

- 🎤 **Voice AI Pipeline**: Complete STT → LLM → TTS pipeline for real-time voice interaction
- 🚀 **Ultra-fast TTS**: Murf Falcon integration for consistently low-latency speech synthesis
- 🧠 **Gemini 2.5 Flash**: Fast, intelligent LLM responses
- 🌍 **Multilingual Support**: LiveKit's multilingual turn detection
- 🔇 **Noise Cancellation**: Background voice cancellation for cleaner audio
- ⚡ **Preemptive Generation**: LLM generates responses while waiting for end of turn
- 📊 **Metrics & Logging**: Integrated performance metrics collection
- 🐳 **Production Ready**: Dockerfile included for deployment

## Dev Setup

### Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) package manager

### Install Dependencies

```console
cd backend
uv sync
```

### Configure Environment

Copy `.env.example` to `.env.local` and set your credentials:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
GOOGLE_API_KEY=your-google-api-key
MURF_API_KEY=your-murf-api-key
CARTESIA_API_KEY=your-cartesia-api-key
```

For LiveKit Cloud users, automatically populate credentials:

```bash
lk cloud auth
lk app env -w -d .env.local
```

## Run the Agent

### 1. Download Required Models

Download VAD and turn detector models:

```console
uv run python src/agent.py download-files
```

### 2. Console Mode (Terminal Testing)

Speak to your agent directly in your terminal:

```console
uv run python src/agent.py console
```

### 3. Development Mode (With Frontend)

Run the agent for use with a frontend:

```console
uv run python src/agent.py dev
```

### 4. Production Mode

```console
uv run python src/agent.py start
```

## Tests

Run the test suite with pytest:

```console
uv run pytest
```

See the [LiveKit testing documentation](https://docs.livekit.io/agents/build/testing/) for more information about testing voice agents.

## Code Formatting

This project uses [Ruff](https://docs.astral.sh/ruff/) for formatting and linting:

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check
```

## Customization

### Modifying the Agent

Edit the `Assistant` class in `src/agent.py`:

```python
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""Your custom instructions here...""",
        )
```

### Adding Tools

Uncomment and modify the example tool in `src/agent.py`:

```python
from livekit.agents import function_tool, RunContext

@function_tool
async def lookup_weather(self, context: RunContext, location: str):
    """Tool description..."""
    return "weather data"
```

### Changing Voice Providers

Swap STT, LLM, or TTS providers in the `AgentSession` setup:

```python
session = AgentSession(
    stt=cartesia.STT(model="ink-whisper"),
    llm=google.LLM(model="gemini-2.5-flash"),
    tts=murf.TTS(voice="en-US-matthew", style="Conversation"),
    # ...
)
```

## Coding Agents & MCP

This project is optimized for coding agents like [Cursor](https://www.cursor.com/) and [Claude Code](https://www.anthropic.com/claude-code).

Install the [LiveKit Docs MCP server](https://docs.livekit.io/mcp) for better AI assistance:

| Tool | Installation |
|------|-------------|
| **Cursor** | [![Install MCP Server](https://cursor.com/deeplink/mcp-install-light.svg)](https://cursor.com/en-US/install-mcp?name=livekit-docs&config=eyJ1cmwiOiJodHRwczovL2RvY3MubGl2ZWtpdC5pby9tY3AifQ%3D%3D) |
| **Claude Code** | `claude mcp add --transport http livekit-docs https://docs.livekit.io/mcp` |
| **Codex CLI** | `codex mcp add --url https://docs.livekit.io/mcp livekit-docs` |
| **Gemini CLI** | `gemini mcp add --transport http livekit-docs https://docs.livekit.io/mcp` |

See [AGENTS.md](AGENTS.md) for guidance on AI assistants working with this codebase.

## Documentation & Resources

- [Murf Falcon TTS Documentation](https://murf.ai/api/docs/text-to-speech/streaming)
- [LiveKit Agents Documentation](https://docs.livekit.io/agents)
- [LiveKit Agents Models](https://docs.livekit.io/agents/models)
- [LiveKit Turn Detection](https://docs.livekit.io/agents/build/turns/turn-detector/)
- [LiveKit Metrics & Logging](https://docs.livekit.io/agents/build/metrics/)

## Deployment

This project includes a production-ready `Dockerfile`. See the [deploying to production](https://docs.livekit.io/agents/ops/deployment/) guide.

### Self-Hosted LiveKit

For self-hosting instead of LiveKit Cloud, see the [self-hosting guide](https://docs.livekit.io/home/self-hosting/). You'll need to use [model plugins](https://docs.livekit.io/agents/models/#plugins) and remove the LiveKit Cloud noise cancellation plugin.

## License

MIT License - see the [LICENSE](LICENSE) file for details.

---

Built for the AI Voice Agents Challenge by [murf.ai](https://murf.ai)
