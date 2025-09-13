import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Chessboard } from "react-chessboard";
import { Chess } from "chess.js";
import { gamesApi } from "../utils/api";
import {
  ArrowLeft,
  Play,
  BarChart3,
  Brain,
  ChevronLeft,
  ChevronRight,
  SkipBack,
  SkipForward,
  TrendingUp,
  MessageSquare,
  GitBranch,
} from "lucide-react";

const GameDetailPage = () => {
  const { gameId } = useParams();
  const [currentMoveIndex, setCurrentMoveIndex] = useState(0);
  const [chess] = useState(new Chess());
  const [gameLoaded, setGameLoaded] = useState(false);
  const [moves, setMoves] = useState([]);
  const [currentPosition, setCurrentPosition] = useState(
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
  );
  const [moveAnalysis, setMoveAnalysis] = useState(null);
  const [analyzingMove, setAnalyzingMove] = useState(null);

  // Auto-analysis toggles - enabled by default
  const [autoAnalysisEnabled, setAutoAnalysisEnabled] = useState(true);
  const [autoAIAnalysisEnabled, setAutoAIAnalysisEnabled] = useState(true);

  // Variation exploration state
  const [isExploringVariation, setIsExploringVariation] = useState(false);
  const [variationAnalysis, setVariationAnalysis] = useState(null);
  const [variationMoveIndex, setVariationMoveIndex] = useState(0);
  const [variationStartFen, setVariationStartFen] = useState(null);
  const [exploringVariation, setExploringVariation] = useState(null);

  const queryClient = useQueryClient();

  const { data: game, isLoading: gameLoading } = useQuery({
    queryKey: ["game", gameId],
    queryFn: () => gamesApi.getGame(gameId),
  });

  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ["analysis", gameId],
    queryFn: () => gamesApi.getGameAnalysis(gameId),
    enabled: !!game,
  });

  // New mutation for analyzing specific moves
  const moveAnalysisMutation = useMutation({
    mutationFn: ({ gameId, moveIndex }) =>
      gamesApi.analyzeMove(gameId, moveIndex),
    onSuccess: (data, variables) => {
      // Ensure data has the expected structure
      if (data && typeof data === "object") {
        setMoveAnalysis({
          eval: data.eval ?? null,
          explanation: data.explanation ?? null,
          variations: Array.isArray(data.variations) ? data.variations : [],
        });
      } else {
        console.warn("Unexpected analysis data structure:", data);
        setMoveAnalysis(null);
      }
      setAnalyzingMove(null);
    },
    onError: (error) => {
      console.error("Move analysis error:", error);
      setAnalyzingMove(null);
      setMoveAnalysis(null);
    },
  });

  // Mutation for exploring variations
  const variationExplorationMutation = useMutation({
    mutationFn: ({ startFen, variationMoves }) =>
      gamesApi.exploreVariation(startFen, variationMoves),
    onSuccess: (data) => {
      setVariationAnalysis(data.variation_analysis);
      setExploringVariation(null);
    },
    onError: (error) => {
      console.error("Variation exploration error:", error);
      setExploringVariation(null);
    },
  });

  // Load game when data is available
  useEffect(() => {
    if (game?.pgn_content && !gameLoaded) {
      try {
        chess.reset();
        chess.loadPgn(game.pgn_content);
        const history = chess.history({ verbose: true });
        setMoves(history);
        setGameLoaded(true);

        // Reset to starting position
        chess.reset();
        setCurrentPosition(chess.fen());
      } catch (error) {
        console.error("Error loading PGN:", error);
      }
    }
  }, [game, gameLoaded, chess]);

  // Update board position when move index changes
  useEffect(() => {
    if (moves.length > 0) {
      chess.reset();
      for (let i = 0; i < currentMoveIndex; i++) {
        chess.move(moves[i]);
      }
      setCurrentPosition(chess.fen());
    }
  }, [currentMoveIndex, moves, chess]);

  const goToMove = (moveIndex) => {
    const newIndex = Math.max(0, Math.min(moveIndex, moves.length));
    setCurrentMoveIndex(newIndex);
    // Clear previous move analysis when navigating
    setMoveAnalysis(null);
  };

  const handleMoveClick = async (moveIndex) => {
    // Navigate to the move first
    goToMove(moveIndex);

    // Then analyze the move if auto-analysis is enabled
    if (gameId && moveIndex > 0 && autoAnalysisEnabled) {
      // Don't analyze starting position
      setAnalyzingMove(moveIndex);
      setMoveAnalysis(null);
      try {
        moveAnalysisMutation.mutate({ gameId, moveIndex });
      } catch (error) {
        console.error("Error triggering move analysis:", error);
        setAnalyzingMove(null);
      }
    }
  };

  // Mutation for limited position analysis
  const limitedAnalysisMutation = useMutation({
    mutationFn: ({ gameId, startMove, useLLM }) =>
      gamesApi.analyzeLimitedPositions(gameId, startMove, useLLM),
    onSuccess: () => {
      queryClient.invalidateQueries(["analysis", gameId]);
    },
  });

  // Auto-analyze current and next 2 positions when moving
  useEffect(() => {
    if (
      autoAnalysisEnabled &&
      gameId &&
      currentMoveIndex > 0 &&
      moves.length > 0
    ) {
      // Trigger limited analysis for current position and next 2
      limitedAnalysisMutation.mutate({
        gameId,
        startMove: currentMoveIndex,
        useLLM: autoAIAnalysisEnabled,
      });
    }
  }, [
    currentMoveIndex,
    autoAnalysisEnabled,
    autoAIAnalysisEnabled,
    gameId,
    moves.length,
  ]);

  const handleVariationExplore = async (variationMoves, moveIndex) => {
    try {
      // Get the current position FEN for the variation start
      const tempChess = new Chess();
      for (let i = 0; i < moveIndex; i++) {
        tempChess.move(moves[i]);
      }
      const startFen = tempChess.fen();

      setVariationStartFen(startFen);
      setExploringVariation(variationMoves);
      setIsExploringVariation(true);
      setVariationMoveIndex(0);

      // Request variation analysis
      variationExplorationMutation.mutate({ startFen, variationMoves });
    } catch (error) {
      console.error("Error exploring variation:", error);
    }
  };

  const exitVariationExploration = () => {
    setIsExploringVariation(false);
    setVariationAnalysis(null);
    setVariationMoveIndex(0);
    setVariationStartFen(null);
    setExploringVariation(null);

    // Return to main game position
    const tempChess = new Chess();
    for (let i = 0; i < currentMoveIndex; i++) {
      tempChess.move(moves[i]);
    }
    setCurrentPosition(tempChess.fen());
  };

  const goToVariationMove = (variationMoveIdx) => {
    if (!variationAnalysis || !variationStartFen) return;

    setVariationMoveIndex(
      Math.max(0, Math.min(variationMoveIdx, variationAnalysis.length))
    );

    if (variationMoveIdx === 0) {
      setCurrentPosition(variationStartFen);
    } else {
      const variationMove = variationAnalysis[variationMoveIdx - 1];
      if (variationMove) {
        setCurrentPosition(variationMove.fen);
      }
    }
  };

  const getCurrentAnalysis = () => {
    if (!analysis || currentMoveIndex === 0) return null;
    return analysis.find((a) => a.move_number === currentMoveIndex);
  };

  if (gameLoading) {
    return <div className="loading">Loading game...</div>;
  }

  if (!game) {
    return <div className="error">Game not found</div>;
  }

  const currentAnalysis = getCurrentAnalysis();

  return (
    <div>
      {/* Header */}
      <div className="card">
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "15px",
            marginBottom: "10px",
          }}
        >
          <Link to="/games" className="btn btn-secondary">
            <ArrowLeft size={16} />
          </Link>
          <div>
            <h1 style={{ margin: 0 }}>{game.title}</h1>
            <div
              style={{
                display: "flex",
                gap: "20px",
                marginTop: "5px",
                fontSize: "14px",
                color: "#666",
              }}
            >
              {game.white_player && <span>White: {game.white_player}</span>}
              {game.black_player && <span>Black: {game.black_player}</span>}
              {game.result && <span>Result: {game.result}</span>}
              {game.date_played && <span>Date: {game.date_played}</span>}
            </div>
          </div>
        </div>

        {limitedAnalysisMutation.error && (
          <div className="error" style={{ marginTop: "10px" }}>
            Error analyzing positions:{" "}
            {limitedAnalysisMutation.error.response?.data?.detail ||
              limitedAnalysisMutation.error.message}
          </div>
        )}
      </div>

      {/* Redesigned Layout */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "15px",
          marginTop: "20px",
        }}
      >
        {/* Top Row - Chessboard and Analysis Panels */}
        <div style={{ display: "flex", gap: "15px" }}>
          {/* Left Panel - Larger Chessboard */}
          <div style={{ flex: "0 0 600px" }}>
            <div className="card" style={{ padding: "20px" }}>
              <Chessboard
                position={currentPosition}
                arePiecesDraggable={false}
                boardWidth={560}
              />

              {/* Move Navigation */}
              <div
                style={{
                  marginTop: "20px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "10px",
                }}
              >
                <button
                  onClick={() => goToMove(0)}
                  className="btn btn-secondary"
                  disabled={currentMoveIndex === 0}
                  style={{ padding: "10px 14px" }}
                >
                  <SkipBack size={18} />
                </button>
                <button
                  onClick={() => goToMove(currentMoveIndex - 1)}
                  className="btn btn-secondary"
                  disabled={currentMoveIndex === 0}
                  style={{ padding: "10px 14px" }}
                >
                  <ChevronLeft size={18} />
                </button>
                <span
                  style={{
                    minWidth: "140px",
                    textAlign: "center",
                    fontWeight: "600",
                    fontSize: "16px",
                  }}
                >
                  Move {currentMoveIndex} / {moves.length}
                </span>
                <button
                  onClick={() => goToMove(currentMoveIndex + 1)}
                  className="btn btn-secondary"
                  disabled={currentMoveIndex >= moves.length}
                  style={{ padding: "10px 14px" }}
                >
                  <ChevronRight size={18} />
                </button>
                <button
                  onClick={() => goToMove(moves.length)}
                  className="btn btn-secondary"
                  disabled={currentMoveIndex >= moves.length}
                  style={{ padding: "10px 14px" }}
                >
                  <SkipForward size={18} />
                </button>
              </div>
            </div>
          </div>

          {/* Right Panel - Analysis Windows */}
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              gap: "15px",
            }}
          >
            {/* Engine Analysis Window */}
            <div className="card" style={{ padding: "20px", flex: 1 }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "15px",
                }}
              >
                <h3
                  style={{ margin: 0, display: "flex", alignItems: "center" }}
                >
                  <BarChart3 size={20} style={{ marginRight: "10px" }} />
                  Engine Analysis
                </h3>
                <label
                  style={{
                    display: "flex",
                    alignItems: "center",
                    cursor: "pointer",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={autoAnalysisEnabled}
                    onChange={(e) => setAutoAnalysisEnabled(e.target.checked)}
                    style={{
                      marginRight: "8px",
                      width: "20px",
                      height: "20px",
                      accentColor: "#28a745",
                    }}
                  />
                  <span style={{ fontSize: "15px", fontWeight: "500" }}>
                    Auto-analyze
                  </span>
                </label>
              </div>

              {moveAnalysis?.eval != null && (
                <div style={{ marginBottom: "20px" }}>
                  <div
                    style={{
                      fontSize: "28px",
                      fontWeight: "bold",
                      marginBottom: "8px",
                      color:
                        moveAnalysis.eval > 0
                          ? "#28a745"
                          : moveAnalysis.eval < 0
                          ? "#dc3545"
                          : "#6c757d",
                    }}
                  >
                    {moveAnalysis.eval > 0 ? "+" : ""}
                    {moveAnalysis.eval.toFixed(2)}
                  </div>
                  <div style={{ fontSize: "14px", color: "#666" }}>
                    {moveAnalysis.eval > 1
                      ? "White is winning"
                      : moveAnalysis.eval > 0.5
                      ? "White is better"
                      : moveAnalysis.eval > -0.5
                      ? "Equal position"
                      : moveAnalysis.eval > -1
                      ? "Black is better"
                      : "Black is winning"}
                  </div>
                </div>
              )}

              {moveAnalysis?.variations &&
                moveAnalysis.variations.length > 0 && (
                  <div>
                    <h4
                      style={{
                        fontSize: "16px",
                        marginBottom: "12px",
                        fontWeight: "600",
                      }}
                    >
                      Top 3 Engine Lines:
                    </h4>
                    {moveAnalysis.variations
                      .slice(0, 3)
                      .map((variation, index) => (
                        <div
                          key={index}
                          style={{
                            padding: "12px 14px",
                            backgroundColor: "#f8f9fa",
                            border: "1px solid #e9ecef",
                            borderRadius: "6px",
                            margin: "8px 0",
                            fontFamily: "monospace",
                            fontSize: "14px",
                            cursor: "pointer",
                            transition: "all 0.2s ease",
                          }}
                          onClick={() =>
                            handleVariationExplore(variation, currentMoveIndex)
                          }
                          onMouseEnter={(e) => {
                            e.target.style.backgroundColor = "#e9ecef";
                            e.target.style.borderColor = "#007bff";
                          }}
                          onMouseLeave={(e) => {
                            e.target.style.backgroundColor = "#f8f9fa";
                            e.target.style.borderColor = "#e9ecef";
                          }}
                        >
                          <div
                            style={{
                              fontWeight: "600",
                              marginBottom: "4px",
                              color: "#495057",
                            }}
                          >
                            Line {index + 1}:
                          </div>
                          <div style={{ color: "#6c757d" }}>
                            {variation.length > 80
                              ? variation.substring(0, 80) + "..."
                              : variation}
                          </div>
                        </div>
                      ))}
                  </div>
                )}

              {!moveAnalysis && currentMoveIndex > 0 && autoAnalysisEnabled && (
                <div
                  style={{
                    textAlign: "center",
                    color: "#666",
                    padding: "40px 20px",
                  }}
                >
                  <BarChart3
                    size={32}
                    style={{ opacity: 0.3, marginBottom: "10px" }}
                  />
                  <div>Click on a move to see engine analysis</div>
                </div>
              )}

              {!autoAnalysisEnabled && (
                <div
                  style={{
                    textAlign: "center",
                    color: "#666",
                    padding: "40px 20px",
                  }}
                >
                  <BarChart3
                    size={32}
                    style={{ opacity: 0.3, marginBottom: "10px" }}
                  />
                  <div>Enable auto-analysis to see engine evaluations</div>
                </div>
              )}
            </div>

            {/* AI Analysis Window */}
            <div className="card" style={{ padding: "20px", flex: 1 }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "15px",
                }}
              >
                <h3
                  style={{ margin: 0, display: "flex", alignItems: "center" }}
                >
                  <Brain size={20} style={{ marginRight: "10px" }} />
                  AI Analysis
                </h3>
                <label
                  style={{
                    display: "flex",
                    alignItems: "center",
                    cursor: "pointer",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={autoAIAnalysisEnabled}
                    onChange={(e) => setAutoAIAnalysisEnabled(e.target.checked)}
                    style={{
                      marginRight: "8px",
                      width: "20px",
                      height: "20px",
                      accentColor: "#007bff",
                    }}
                  />
                  <span style={{ fontSize: "15px", fontWeight: "500" }}>
                    Auto-analyze
                  </span>
                </label>
              </div>

              {autoAIAnalysisEnabled && moveAnalysis?.explanation && (
                <div
                  style={{
                    padding: "16px",
                    backgroundColor: "#f8fbff",
                    borderRadius: "8px",
                    border: "1px solid #b3d9ff",
                    lineHeight: "1.6",
                    fontSize: "15px",
                  }}
                >
                  {moveAnalysis.explanation}
                </div>
              )}

              {autoAIAnalysisEnabled &&
                !moveAnalysis?.explanation &&
                currentMoveIndex > 0 && (
                  <div
                    style={{
                      textAlign: "center",
                      color: "#666",
                      padding: "40px 20px",
                    }}
                  >
                    <Brain
                      size={32}
                      style={{ opacity: 0.3, marginBottom: "10px" }}
                    />
                    <div>Click on a move to see AI explanation</div>
                  </div>
                )}

              {!autoAIAnalysisEnabled && (
                <div
                  style={{
                    textAlign: "center",
                    color: "#666",
                    padding: "40px 20px",
                  }}
                >
                  <Brain
                    size={32}
                    style={{ opacity: 0.3, marginBottom: "10px" }}
                  />
                  <div>Enable auto-analysis to see AI explanations</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Bottom Row - Horizontal Move List */}
        <div className="card" style={{ padding: "20px" }}>
          <h3 style={{ marginBottom: "15px", fontSize: "18px" }}>
            Game Moves ({moves.length} moves)
          </h3>

          {moves.length === 0 ? (
            <div
              style={{ padding: "40px", textAlign: "center", color: "#666" }}
            >
              No moves found. Loading game...
            </div>
          ) : (
            <div
              style={{
                maxHeight: "150px",
                overflowY: "auto",
                border: "1px solid #e9ecef",
                borderRadius: "8px",
                padding: "15px",
              }}
            >
              {/* Horizontal Chess.com style move list */}
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "6px",
                  alignItems: "center",
                }}
              >
                {moves.map((move, index) => {
                  const moveNumber = index + 1;
                  const isCurrentMove = moveNumber === currentMoveIndex;
                  const isAnalyzing = analyzingMove === moveNumber;
                  const pairNumber = Math.ceil(moveNumber / 2);
                  const isWhiteMove = index % 2 === 0;

                  return (
                    <React.Fragment key={index}>
                      {isWhiteMove && (
                        <span
                          style={{
                            color: "#666",
                            fontSize: "15px",
                            fontWeight: "600",
                            marginRight: "6px",
                            userSelect: "none",
                            minWidth: "24px",
                          }}
                        >
                          {pairNumber}.
                        </span>
                      )}
                      <div
                        style={{
                          padding: "6px 12px",
                          cursor: "pointer",
                          backgroundColor: isCurrentMove
                            ? "#007bff"
                            : "transparent",
                          color: isCurrentMove ? "white" : "inherit",
                          borderRadius: "4px",
                          border: isAnalyzing
                            ? "2px solid #ffc107"
                            : "1px solid transparent",
                          transition: "all 0.2s ease",
                          fontFamily: "monospace",
                          fontSize: "15px",
                          fontWeight: "500",
                          marginRight: "6px",
                          position: "relative",
                        }}
                        onClick={() => handleMoveClick(moveNumber)}
                        onMouseEnter={(e) => {
                          if (!isCurrentMove) {
                            e.target.style.backgroundColor = "#f8f9fa";
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!isCurrentMove) {
                            e.target.style.backgroundColor = "transparent";
                          }
                        }}
                      >
                        {move.san}
                        {isAnalyzing && (
                          <span style={{ fontSize: "11px", marginLeft: "4px" }}>
                            🔍
                          </span>
                        )}
                      </div>
                    </React.Fragment>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Variation Exploration (keep existing) */}
      {isExploringVariation && (
        <div className="card" style={{ marginTop: "15px", padding: "20px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "15px",
            }}
          >
            <h3 style={{ margin: 0, display: "flex", alignItems: "center" }}>
              <GitBranch size={18} style={{ marginRight: "8px" }} />
              Exploring Variation
            </h3>
            <button
              onClick={exitVariationExploration}
              className="btn btn-secondary"
              style={{ padding: "8px 16px" }}
            >
              Exit Variation
            </button>
          </div>
          {/* Keep existing variation exploration content */}
        </div>
      )}
    </div>
  );
};

export default GameDetailPage;
