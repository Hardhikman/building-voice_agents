# Ten Days of Voice Agents 2025

Welcome to the **Ten Days of Voice Agents Challenge** by [murf.ai](https://murf.ai)!

## About the Challenge

We just launched **Murf Falcon** – the consistently fastest TTS API, and you're going to be among the first to test it out in ways never thought before!

**Build 10 AI Voice Agents over the course of 10 Days** along with help from our devs and the community champs, and win rewards!

### How It Works

- One task is provided every day along with a GitHub repo for reference
- Build a voice agent with specific personas and skills
- Post on GitHub and share with the world on LinkedIn!

## Repository Structure

This is a **monorepo** that contains both the backend and frontend for building voice agent applications. It's designed to be your starting point for each day's challenge task.

```
ten-days-of-voice-agents-2025/
├── backend/              # LiveKit Agents backend with Murf Falcon TTS
│   └── src/
│       ├── agent.py              # Main wellness agent
│       ├── agent_food_ordering.py # Food ordering agent (Day 2)
│       ├── agent_game_master.py   # Game master agent (Day 3)
│       ├── agent_sdr.py           # SDR/Sales agent (Day 4)
│       └── db.py                  # Database utilities
├── frontend/             # React/Next.js frontend for voice interaction
├── challenges/           # Daily challenge task descriptions
│   ├── Day 1 Task.md
│   ├── Day 2 Task.md
│   ├── Day 3 Task.md
│   ├── Day 4 Task.md
│   ├── Day 5 Task.md
│   ├── Day 7 Task.md
│   ├── Day 8 Task.md
│   └── Day 10 Task.md
├── bin/                  # Pre-built LiveKit server binary (Windows)
├── start_app.ps1         # PowerShell script to start all services (Windows)
├── install_livekit.ps1   # LiveKit server installation script (Windows)
└── README.md             # This file
```

### Backend

The backend is based on [LiveKit's agent-starter-python](https://github.com/livekit-examples/agent-starter-python) with modifications to integrate **Murf Falcon TTS** for ultra-fast, high-quality voice synthesis.

**Tech Stack:**

| Component | Provider | Model |
|-----------|----------|-------|
| **STT** (Speech-to-Text) | Cartesia | `ink-whisper` |
| **LLM** (Large Language Model) | Google | `gemini-2.5-flash` |
| **TTS** (Text-to-Speech) | Murf Falcon | `en-US-matthew` |
| **VAD** (Voice Activity Detection) | Silero | Default |
| **Turn Detection** | LiveKit | Multilingual Model |

**Features:**

- 🎤 Complete voice AI pipeline (STT → LLM → TTS)
- 🚀 Murf Falcon TTS integration for ultra-fast speech synthesis
- 🧠 Google Gemini 2.5 Flash for intelligent responses
- 🌍 Multilingual turn detection support
- 🔇 Background voice cancellation
- ⚡ Preemptive generation for low latency
- 📊 Integrated metrics and logging
- 🐳 Production-ready Dockerfile

**Agent Implementations:**

- `agent.py` - Wellness coach agent (Day 1)
- `agent_food_ordering.py` - Food ordering assistant (Day 2)
- `agent_game_master.py` - Interactive game master (Day 3)
- `agent_sdr.py` - Sales development representative (Day 4)

[→ Backend Documentation](./backend/README.md)

### Frontend

The frontend is based on [LiveKit's agent-starter-react](https://github.com/livekit-examples/agent-starter-react), providing a modern, beautiful UI for interacting with your voice agents.

**Features:**

- Real-time voice interaction with LiveKit Agents
- Camera video streaming support
- Screen sharing capabilities
- Audio visualization and level monitoring
- Light/dark theme switching
- Highly customizable branding and UI

[→ Frontend Documentation](./frontend/README.md)

## Quick Start

### Prerequisites

Make sure you have the following installed:

- Python 3.9+ with [uv](https://docs.astral.sh/uv/) package manager
- Node.js 18+ with pnpm
- [LiveKit CLI](https://docs.livekit.io/home/cli/cli-setup) (optional but recommended)

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd ten-days-of-voice-agents-2025
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Copy environment file and configure
cp .env.example .env.local

# Edit .env.local with your credentials:
# - LIVEKIT_URL
# - LIVEKIT_API_KEY
# - LIVEKIT_API_SECRET
# - MURF_API_KEY (for Falcon TTS)
# - GOOGLE_API_KEY (for Gemini LLM)
# - CARTESIA_API_KEY (for Cartesia STT)

# Download required models
uv run python src/agent.py download-files
```

For LiveKit Cloud users, you can automatically populate credentials:

```bash
lk cloud auth
lk app env -w -d .env.local
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Copy environment file and configure
cp .env.example .env.local

# Edit .env.local with the same LiveKit credentials
```

### 4. Run the Application

#### Windows (PowerShell)

Use the convenience script to start all services:

```powershell
# From the root directory
.\start_app.ps1
```

This will start:
- LiveKit Server (from `bin/livekit-server.exe`)
- Backend agent (listening for connections)
- Frontend app (at http://localhost:3000)

#### Manual Start (All Platforms)

```bash
# Terminal 1 - LiveKit Server
# Windows: .\bin\livekit-server.exe --dev
# Mac/Linux: livekit-server --dev

# Terminal 2 - Backend Agent
cd backend
uv run python src/agent.py dev

# Terminal 3 - Frontend
cd frontend
pnpm dev
```

Then open http://localhost:3000 in your browser!

## Daily Challenge Tasks

Check the `challenges/` directory for daily task descriptions. Each day builds upon your voice agent with new capabilities:

| Day | Task | Agent |
|-----|------|-------|
| 1 | Wellness Coach | `agent.py` |
| 2 | Food Ordering | `agent_food_ordering.py` |
| 3 | Game Master | `agent_game_master.py` |
| 4 | SDR/Sales | `agent_sdr.py` |
| 5-10 | Advanced Challenges | See `challenges/` |

## Documentation & Resources

- [Murf Falcon TTS Documentation](https://murf.ai/api/docs/text-to-speech/streaming)
- [LiveKit Agents Documentation](https://docs.livekit.io/agents)
- [LiveKit Agents Models](https://docs.livekit.io/agents/models)
- [Original Backend Template](https://github.com/livekit-examples/agent-starter-python)
- [Original Frontend Template](https://github.com/livekit-examples/agent-starter-react)

## Testing

The backend includes a test suite:

```bash
cd backend
uv run pytest
```

Learn more about testing voice agents in the [LiveKit testing documentation](https://docs.livekit.io/agents/build/testing/).

## Contributing & Community

This is a challenge repository, but we encourage collaboration and knowledge sharing!

- Share your solutions and learnings on GitHub
- Post about your progress on LinkedIn
- Join the [LiveKit Community Slack](https://livekit.io/join-slack)
- Connect with other challenge participants

## License

This project is based on MIT-licensed templates from LiveKit and includes integration with Murf Falcon. See individual LICENSE files in backend and frontend directories for details.

## Have Fun!

Remember, the goal is to learn, experiment, and build amazing voice AI agents. Don't hesitate to be creative and push the boundaries of what's possible with Murf Falcon and LiveKit!

Good luck with the challenge!

---

Built for the Ten Days of Voice Agents Challenge by [murf.ai](https://murf.ai)
