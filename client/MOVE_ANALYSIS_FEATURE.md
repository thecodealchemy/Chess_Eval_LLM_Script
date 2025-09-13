# Move Analysis Feature - React Frontend

## Overview

The React frontend now includes an enhanced game detail page with interactive move analysis functionality. Users can click on any move to get detailed AI-powered analysis including engine evaluation, explanations, and top variations.

## Features

### 🎯 Interactive Move Analysis

- **Click-to-Analyze**: Click any move in the move list to get instant analysis
- **Real-time Feedback**: Visual indicators show when a move is being analyzed
- **Persistent Results**: Analysis results are cached and persist during navigation

### 📊 Engine Evaluation Display

- **Visual Evaluation**: Color-coded evaluation display (green for White advantage, red for Black)
- **Precise Values**: Centipawn evaluation converted to pawn values
- **Positional Assessment**: Descriptive text explaining the position status

### 🤖 AI-Powered Explanations

- **Groq LLM Integration**: Human-readable move explanations using Llama 3 8B model
- **Contextual Analysis**: Explanations consider position, evaluation, and tactical factors
- **Concise Format**: Optimized for quick understanding (under 150 characters)

### 🎲 Variation Analysis

- **Top Variations**: Best move sequences from Lichess Cloud Eval
- **Multiple Lines**: Shows up to 3 best variations
- **Standard Notation**: Variations displayed in algebraic notation

## User Interface

### Enhanced Move List

```jsx
// Interactive move list with analysis status
<div className="move-list">
  {moves.map((move, index) => (
    <div
      className={`move-item ${isAnalyzing ? "analyzing" : ""} ${
        isAnalyzed ? "analyzed" : ""
      }`}
      onClick={() => handleMoveClick(moveIndex)}
    >
      {moveNumber}. {move.san}
      {isAnalyzing && <span>🔍 Analyzing...</span>}
      {isAnalyzed && <span>✓ Analyzed</span>}
    </div>
  ))}
</div>
```

### Analysis Display Panel

```jsx
// Comprehensive analysis results
<div className="analysis-panel">
  <div className="eval-display">
    <TrendingUp /> Engine Evaluation: +0.75
  </div>

  <div className="explanation-box">
    <MessageSquare /> AI Explanation: "White gains advantage with central
    control..."
  </div>

  <div className="variations-list">
    <GitBranch /> Top Variations:
    {variations.map((variation) => (
      <div className="variation-item">{variation}</div>
    ))}
  </div>
</div>
```

## API Integration

### Move Analysis Endpoint

```javascript
// New API function in utils/api.js
analyzeMove: async (gameId, moveIndex) => {
  const response = await api.post("/analyse_move", {
    game_id: gameId,
    move_index: moveIndex,
  });
  return response.data;
};
```

### React Query Integration

```javascript
// Move analysis mutation
const moveAnalysisMutation = useMutation({
  mutationFn: ({ gameId, moveIndex }) =>
    gamesApi.analyzeMove(gameId, moveIndex),
  onSuccess: (data) => {
    setMoveAnalysis(data);
    setAnalyzingMove(null);
  },
});
```

## State Management

### Component State

```javascript
const [moveAnalysis, setMoveAnalysis] = useState(null);
const [analyzingMove, setAnalyzingMove] = useState(null);
const [currentMoveIndex, setCurrentMoveIndex] = useState(0);
```

### Analysis Flow

1. User clicks a move in the move list
2. Component navigates to that move position
3. API request sent to `/analyse_move` endpoint
4. Loading state displayed during analysis
5. Results displayed in analysis panel
6. Results cached for future reference

## Visual Feedback

### Loading States

- **Move List**: Yellow border indicates analyzing move
- **Analysis Panel**: Loading spinner with "Analyzing move X..." message
- **Button States**: Disabled during analysis

### Success States

- **Move List**: Green checkmark for analyzed moves
- **Analysis Panel**: Full results with color-coded evaluation
- **Visual Indicators**: Icons for different types of information

### Error Handling

- **Network Errors**: Graceful error messages
- **Invalid Moves**: Validation feedback
- **API Failures**: Fallback to basic information

## Styling and UX

### CSS Classes

```css
.move-item {
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.move-item:hover {
  border-left-color: #007bff;
  transform: translateX(2px);
}

.move-item.analyzing {
  border-left-color: #ffc107;
  animation: pulse 1.5s infinite;
}

.eval-display {
  font-size: 28px;
  font-weight: bold;
  text-align: center;
  padding: 15px;
  border-radius: 6px;
}

.explanation-box {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  padding: 15px;
  font-style: italic;
}
```

### Responsive Design

- **Mobile-First**: Works on all screen sizes
- **Flexible Layout**: Adapts to different viewport widths
- **Touch-Friendly**: Large click targets for mobile users

## Performance Optimizations

### Caching Strategy

- **Backend Caching**: MongoDB cache prevents redundant API calls
- **Frontend Caching**: Results persist during session
- **Selective Updates**: Only re-render affected components

### API Efficiency

- **Single Move Analysis**: Only analyze clicked moves
- **Debounced Requests**: Prevent rapid-fire API calls
- **Error Recovery**: Retry logic for failed requests

## Usage Instructions

### For Users

1. Navigate to any game detail page
2. Click "Game Moves - Click to Analyze" section
3. Click any move number to get analysis
4. View results in the analysis panel above
5. Navigate between moves to compare analyses

### For Developers

1. Component located in `src/pages/GameDetailPage.jsx`
2. API utilities in `src/utils/api.js`
3. Styling in `src/index.css`
4. Test with `client/test_move_analysis.py`

## Testing

### Manual Testing

```bash
# Start the development servers
npm run dev  # Frontend
python server/run_server.py  # Backend

# Upload a test game
python client/test_move_analysis.py

# Open the game detail page and test move analysis
```

### Automated Testing

```javascript
// Test move analysis functionality
test("should analyze move when clicked", async () => {
  const { getByText } = render(<GameDetailPage />);
  const move = getByText("1. e4");

  fireEvent.click(move);

  await waitFor(() => {
    expect(getByText(/Analyzing move/)).toBeInTheDocument();
  });
});
```

## Future Enhancements

### Planned Features

- **Move Comparison**: Compare multiple move analyses
- **Position Search**: Find similar positions in database
- **Opening Book**: Integration with opening theory
- **Analysis History**: Track user's analysis patterns

### Technical Improvements

- **WebSocket Integration**: Real-time analysis updates
- **Service Worker**: Offline analysis caching
- **Progressive Loading**: Lazy load analysis components
- **A/B Testing**: Optimize UI based on user behavior

## Dependencies

### New Dependencies

- **Lucide React Icons**: TrendingUp, MessageSquare, GitBranch
- **Enhanced CSS**: New classes for analysis display
- **React Query**: For mutation management

### Updated Components

- **GameDetailPage**: Enhanced with analysis functionality
- **API Utils**: New analyzeMove function
- **CSS Styles**: Additional classes for visual feedback

The move analysis feature provides a comprehensive, user-friendly way to analyze chess positions with professional-grade evaluation and AI explanations, making it an excellent tool for chess improvement and learning.
