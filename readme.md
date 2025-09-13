# Chess Game Analysis App

A full-stack application for analyzing chess games with engine evaluations and optional AI explanations. Upload PGN files, get move-by-move analysis, and browse your game history with an interactive chess board interface.

## Features

- **PGN Upload**: Upload chess games in PGN format via drag-and-drop or file selection
- **Engine Analysis**: Get position evaluations using Lichess Cloud Evaluation API
- **Interactive Chess Board**: View games with a responsive chessboard component
- **Move Navigation**: Step through games move by move with analysis
- **Game Management**: Browse, analyze, and delete uploaded games
- **AI Explanations**: Optional integration with LLM APIs for human-readable move explanations
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

### Backend

- **FastAPI**: Modern Python web framework
- **MongoDB**: Document database for storing games and analysis
- **Python Chess**: Chess game processing and PGN parsing
- **Motor**: Async MongoDB driver
- **Lichess API**: Cloud-based chess engine evaluation

### Frontend

- **React 18**: Modern React with hooks
- **Vite**: Fast build tool and development server
- **React Router**: Client-side routing
- **TanStack Query**: Data fetching and caching
- **React Chessboard**: Interactive chess board component
- **Chess.js**: Chess game logic and validation
- **Axios**: HTTP client for API calls

### Infrastructure

- **Docker**: Containerized deployment
- **Docker Compose**: Multi-service orchestration

## Project Structure

```
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── utils/          # API utilities
│   │   ├── App.jsx         # Main App component
│   │   └── main.jsx        # Entry point
│   ├── public/             # Static assets
│   ├── package.json        # Frontend dependencies
│   ├── vite.config.js      # Vite configuration
│   └── Dockerfile          # Frontend container
├── server/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI application
│   │   ├── routes.py       # API endpoints
│   │   ├── models.py       # Pydantic models
│   │   ├── database.py     # MongoDB connection
│   │   └── chess_analyzer.py # Chess analysis logic
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment variables template
│   └── Dockerfile          # Backend container
├── docker-compose.yml      # Multi-service setup
└── README.md              # This file
```

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd chess-analysis-app
   ```

2. **Start all services**

   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup

#### Prerequisites

- Python 3.9+
- Node.js 18+
- MongoDB (local or cloud instance)

#### Backend Setup

1. **Navigate to server directory**

   ```bash
   cd server
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB connection string
   ```

5. **Start the backend**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend Setup

1. **Navigate to client directory**

   ```bash
   cd client
   ```

2. **Install dependencies**

   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

#### MongoDB Setup

**Option 1: Local MongoDB**

- Install MongoDB locally
- Start MongoDB service
- Use connection string: `mongodb://localhost:27017`

**Option 2: MongoDB Atlas (Cloud)**

- Create free cluster at mongodb.com
- Get connection string from Atlas dashboard
- Update `MONGODB_URL` in `.env` file

**Option 3: Docker**

```bash
docker run -d -p 27017:27017 --name chess-mongo \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:7.0
```

## API Endpoints

### Games

- `POST /api/v1/games/upload` - Upload a new PGN game
- `POST /api/v1/upload_pgn` - Upload PGN string and get parsed game data
- `POST /api/v1/analyse_move` - Analyze a specific move with AI explanation
- `GET /api/v1/games` - Get list of games
- `GET /api/v1/games/{game_id}` - Get specific game details
- `DELETE /api/v1/games/{game_id}` - Delete a game

### Analysis

- `POST /api/v1/games/{game_id}/analyze` - Analyze a game
- `GET /api/v1/games/{game_id}/analysis` - Get game analysis results

### System

- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## Usage

### 1. Upload a Game

- Navigate to the Upload page
- Enter a title for your game
- Either drag and drop a PGN file or paste PGN content directly
- Click "Upload Game"

### 2. Analyze a Game

- Go to the game detail page
- Click "Analyze Game" for engine evaluation
- Click "Analyze with AI" for additional explanations (requires API key)

### 3. Review Analysis

- Use the chess board to visualize positions
- Navigate through moves using the control buttons
- View evaluations, best moves, and explanations in the analysis panel

### 4. Manage Games

- Browse all games in the Games list
- Delete games you no longer need
- Filter and search through your game history

### 5. Using the /upload_pgn API Endpoint

The `/upload_pgn` endpoint allows you to upload PGN strings directly and get parsed game data:

**Request:**

```json
{
  "pgn": "[Event \"Test Game\"]\n[White \"Alice\"]\n[Black \"Bob\"]\n[Result \"1-0\"]\n\n1. e4 e5 2. Nf3 1-0"
}
```

**Response:**

```json
{
  "game_id": "507f1f77bcf86cd799439011",
  "metadata": {
    "white_player": "Alice",
    "black_player": "Bob",
    "event": "Test Game",
    "result": "1-0",
    "date": null,
    "site": null,
    "round": null,
    "eco": null
  },
  "moves": [
    {
      "move_number": 0,
      "san": "Starting position",
      "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    },
    {
      "move_number": 1,
      "san": "e4",
      "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    },
    {
      "move_number": 2,
      "san": "e5",
      "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
    },
    {
      "move_number": 3,
      "san": "Nf3",
      "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"
    }
  ]
}
```

### 6. Using the /analyse_move API Endpoint

The `/analyse_move` endpoint provides detailed analysis for specific moves using Lichess Cloud Eval and Groq LLM:

**Request:**

```json
{
  "game_id": "507f1f77bcf86cd799439011",
  "move_index": 5
}
```

**Response:**

```json
{
  "eval": 0.75,
  "explanation": "White gains a slight advantage with this central pawn advance, controlling key squares and preparing piece development.",
  "variations": ["d4 exd4 Nxd4 Nc6 Nxc6"]
}
```

**Features:**

- **Lichess Cloud Evaluation**: Professional-grade position analysis
- **AI Explanations**: Human-readable move explanations via Groq LLM
- **MongoDB Caching**: Results are cached to avoid repeated API calls
- **Move Navigation**: Analyze any position in a game by move index

## Configuration

### Environment Variables

Create a `.env` file in the server directory:

```env
# Required: MongoDB connection
MONGODB_URL=mongodb://localhost:27017

# Optional: LLM API keys for explanations
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Frontend Configuration

The frontend is configured via `vite.config.js` to proxy API requests to the backend during development.

## Development

### Running Tests

**Backend Tests**

```bash
cd server
pytest tests/
```

**Frontend Tests**

```bash
cd client
npm test
```

### Code Style

**Backend**

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Document functions and classes

**Frontend**

- Use ESLint configuration
- Follow React best practices
- Use functional components with hooks

### Adding Features

1. **Backend**: Add new endpoints in `routes.py`, models in `models.py`
2. **Frontend**: Create components in `components/`, pages in `pages/`
3. **Database**: Add new collections or fields as needed

## Deployment

### Production Deployment

1. **Update environment variables**

   - Set production MongoDB URL
   - Add API keys for LLM services
   - Configure CORS origins

2. **Build and deploy with Docker**

   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Or deploy separately**
   - Backend: Deploy to services like Railway, Heroku, or AWS
   - Frontend: Deploy to Vercel, Netlify, or similar
   - Database: Use MongoDB Atlas or managed database service

### Environment-Specific Configurations

Create different Docker Compose files or environment configurations for:

- Development (`docker-compose.yml`)
- Production (`docker-compose.prod.yml`)
- Testing (`docker-compose.test.yml`)

## Troubleshooting

### Common Issues

**Connection Errors**

- Check MongoDB connection string
- Ensure MongoDB service is running
- Verify network connectivity between services

**API Errors**

- Check backend logs: `docker-compose logs backend`
- Verify environment variables are set
- Test API endpoints directly at `/docs`

**Frontend Issues**

- Clear browser cache and local storage
- Check console for JavaScript errors
- Verify API proxy configuration in Vite

**Analysis Not Working**

- Check internet connection (Lichess API access required)
- Verify PGN format is valid
- Review backend logs for analysis errors

### Debugging

**Enable Debug Mode**

```bash
# Backend
uvicorn app.main:app --reload --log-level debug

# Frontend
npm run dev -- --debug
```

**View Logs**

```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Database logs
docker-compose logs -f mongodb
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Lichess](https://lichess.org) for providing free cloud evaluation API
- [Chess.js](https://github.com/jhlywa/chess.js) for chess game logic
- [React Chessboard](https://github.com/Clariity/react-chessboard) for the interactive board component
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python web framework
