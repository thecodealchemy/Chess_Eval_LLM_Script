# Groq API Setup Guide

The `/analyse_move` endpoint uses Groq's LLM API to provide intelligent explanations of chess moves. Follow these steps to set up Groq integration.

## 1. Get Groq API Key

1. Visit [https://console.groq.com/](https://console.groq.com/)
2. Sign up for a free account
3. Navigate to API Keys section
4. Generate a new API key
5. Copy the API key (starts with `gsk_...`)

## 2. Configure Environment

Add your Groq API key to the `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file
GROQ_API_KEY=gsk_your_actual_api_key_here
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Test the Integration

Run the example script to test the endpoint:

```bash
python example_analyse_move.py
```

## 5. API Usage

### Basic Move Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/analyse_move" \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "your_game_id",
    "move_index": 1
  }'
```

### Response Format

```json
{
  "eval": 0.25,
  "explanation": "White is slightly better. The e4 move controls the center and opens lines for piece development.",
  "variations": ["e4 e5 Nf3 Nc6 Bb5"]
}
```

## Troubleshooting

### Common Issues

**"Import groq could not be resolved"**

- Solution: Install dependencies with `pip install -r requirements.txt`

**"Error getting Groq explanation"**

- Check your API key is correctly set in `.env`
- Verify your Groq account has API credits
- Check internet connection

**"Fallback explanation used"**

- The endpoint will use simple evaluations if Groq is unavailable
- Check logs for specific Groq API errors

### Rate Limits

Groq free tier includes:

- 30 requests per minute
- 6,000+ tokens per minute

The endpoint is optimized to stay within these limits by:

- Using concise prompts (< 150 characters responses)
- Caching results in MongoDB
- Using efficient Llama 3 8B model

### Cost Optimization

- **Caching**: Results are cached in MongoDB to avoid repeated API calls
- **Efficient Prompts**: Optimized for brevity while maintaining quality
- **Fallback Mode**: Works without Groq if API key is not provided

## Models Available

The endpoint uses `llama3-8b-8192` by default, but you can modify the model in `chess_analyzer.py`:

Available models:

- `llama3-8b-8192` (Fast, good for chess analysis)
- `llama3-70b-8192` (More powerful, higher cost)
- `mixtral-8x7b-32768` (Alternative option)

## Advanced Configuration

### Custom Prompts

Edit `chess_analyzer.py` to customize the analysis prompts:

```python
prompt = f"""
Your custom prompt here...
Position FEN: {fen}
Evaluation: {eval_score}
"""
```

### Temperature Settings

Adjust creativity vs consistency:

- `temperature=0.1` - More consistent, factual
- `temperature=0.5` - Balanced (default)
- `temperature=0.9` - More creative, varied

### Token Limits

Adjust response length:

- `max_tokens=50` - Very brief
- `max_tokens=100` - Standard (default)
- `max_tokens=200` - Detailed

## Support

For Groq-specific issues:

- [Groq Documentation](https://docs.groq.com/)
- [Groq Discord Community](https://discord.gg/groq)

For endpoint issues, check the server logs and test with the example script.
