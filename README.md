# Agentic Lender

An AI-powered lending memo generation system that guides underwriters through structured conversations to create comprehensive credit memos.

## 📋 Overview

The Agentic Lender system consists of:
- **Backend**: FastAPI server with Claude AI integration for intelligent conversation flow
- **Frontend**: React TypeScript application with real-time chat and dynamic summary generation
- **Session Management**: Persistent conversation storage for resuming discussions

## 🛠️ Prerequisites

- **Python 3.8+** (for backend)
- **uv** (Python package manager) - [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **Node.js 16+** (for frontend)
- **Anthropic API Key** (for Claude AI)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd agentic-lender
```

### 2. Backend Setup

#### Install Dependencies
```bash
cd backend
uv sync
```

#### Environment Configuration
Create a `.env` file in the `backend/` directory:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### Start Backend Server
```bash
# Using uv to run the application
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# OR using uv run python
uv run python main.py
```

The backend will be available at: `http://localhost:8000`

### 3. Frontend Setup

#### Install Dependencies
```bash
cd frontend
npm install
```

#### Start Development Server
```bash
npm run dev
```

The frontend will be available at: `http://localhost:3000`

## 📖 API Documentation

Once the backend is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/chat` | Send message to AI agent |
| `POST` | `/generate-summary` | Generate HTML summary |
| `POST` | `/sessions` | Create new session |
| `GET` | `/sessions` | List all sessions |
| `GET` | `/sessions/{id}` | Get specific session |
| `DELETE` | `/sessions/{id}` | Delete session |

## 🗂️ Project Structure

```
agentic-lender/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── templates/
│   │   └── insufficient_data.html  # HTML template for incomplete summaries
│   ├── sessions/               # Session storage directory (auto-created)
│   ├── .env                    # Environment variables (create this)
│   ├── pyproject.toml          # Python dependencies and project config
│   └── uv.lock                 # Dependency lock file
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chatbot.tsx     # Chat interface component
│   │   │   └── Summary.tsx     # Dynamic summary component
│   │   ├── App.tsx             # Main application
│   │   └── main.tsx           # Entry point
│   ├── package.json           # Node.js dependencies
│   └── ...
└── README.md                  # This file
```

## 💬 How It Works

### Conversation Flow
1. **Start Conversation**: User begins chat (auto-creates session)
2. **Guided Questions**: AI agent asks structured questions in flexible order:
   - Credit Summary (Borrower, Financials, Risks)
   - Conditions & Covenants
   - Client Background
   - Pricing & Fees
   - Collateral Analysis
   - Other Information
3. **Dynamic Summary**: Real-time HTML memo generation
4. **Session Persistence**: Conversations saved for later resumption

### Example Conversation
```
Agent: Hello! I'll help you create a credit memo. What information would you like to provide first?

User: The borrower is John Smith, credit score 750, income $80,000

Agent: Great! I have the borrower information. Now, could you tell me about the collateral for this loan?

User: $500K in blue-chip stocks and ETFs, LTV will be 50%

Agent: Perfect. What about the pricing structure for this loan?
```

## 🧪 Testing

### Backend Testing
```bash
cd backend

# Test basic functionality
uv run python test_conversation.py

# Test flexible conversation flow
uv run python test_flexible_flow.py

# Test session management
uv run python test_sessions.py
```

### Frontend Testing
```bash
cd frontend
npm test
```

## 🔧 Configuration

### Backend Configuration
- **AI Model**: Uses Claude 3.5 Sonnet via Agno framework
- **CORS**: Configured for frontend at `localhost:3000`
- **Session Storage**: File-based in `backend/sessions/`
- **Templates**: HTML templates in `backend/templates/`

### Frontend Configuration
- **API Base URL**: `http://localhost:8000`
- **Styling**: Tailwind CSS
- **Build Tool**: Vite

## 📊 Features

### 🤖 AI Agent Features
- **Flexible Conversation Flow**: Adapts to user input order
- **Context Awareness**: Tracks provided information
- **Professional Banking Language**: Industry-appropriate responses
- **Comprehensive Memo Generation**: 8-section structured output

### 💾 Session Management
- **Persistent Storage**: Resume conversations anytime
- **Automatic Titles**: Generated from first user message
- **Message History**: Complete conversation tracking
- **Session Metadata**: Timestamps, status, message counts

### 🎨 Frontend Features
- **Real-time Chat**: Instant AI responses
- **Dynamic Summaries**: Auto-updating HTML memos
- **Responsive Design**: Works on desktop and mobile
- **Loading States**: User-friendly feedback

## 🛡️ Security Notes

- **API Keys**: Store in `.env` file, never commit to version control
- **Session IDs**: Use UUIDs for security
- **CORS**: Configured for development (adjust for production)
- **File Storage**: Sessions stored locally (consider database for production)

## 🚀 Production Deployment

### Backend Deployment
```bash
# Add gunicorn to dependencies
uv add gunicorn

# Run with Gunicorn
uv run gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend Deployment
```bash
# Build for production
npm run build

# Serve static files
npm run preview
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

**Backend won't start:**
- Check Python version (3.8+)
- Verify API key in `.env` file
- Install dependencies: `uv sync`

**Frontend won't start:**
- Check Node.js version (16+)
- Install dependencies: `npm install`
- Check if backend is running on port 8000

**API errors:**
- Verify Anthropic API key is valid
- Check network connectivity
- Review backend logs for errors

**Session issues:**
- Ensure `backend/sessions/` directory exists
- Check file permissions
- Verify JSON file format

### Getting Help

- Check the API documentation at `http://localhost:8000/docs`
- Review the test files for usage examples
- Ensure all environment variables are set correctly

## 📞 Support

For issues and questions, please create an issue in the repository.