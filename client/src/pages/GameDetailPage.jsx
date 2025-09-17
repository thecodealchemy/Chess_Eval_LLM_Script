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
  const [moveArrows, setMoveArrows] = useState([]);

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
      console.log("Move analysis response:", data); // Debug log
      if (data && typeof data === "object") {
        const analysisData = {
          eval: data.eval ?? null,
          explanation: data.explanation ?? null,
          variations: Array.isArray(data.variations) ? data.variations : [],
        };
        console.log("Setting move analysis:", analysisData); // Debug log
        setMoveAnalysis(analysisData);
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

      // Calculate arrow for current move
      const arrows = [];
      if (currentMoveIndex > 0 && moves[currentMoveIndex - 1]) {
        const currentMove = moves[currentMoveIndex - 1];
        console.log("Current move for arrow:", currentMove); // Debug log
        arrows.push([
          currentMove.from,
          currentMove.to,
          "rgb(255, 170, 0)", // Orange color for current move
        ]);
      }
      console.log("Setting move arrows:", arrows); // Debug log
      setMoveArrows(arrows);
    }
  }, [currentMoveIndex, moves, chess]);

  const goToMove = (moveIndex) => {
    const newIndex = Math.max(0, Math.min(moveIndex, moves.length));
    setCurrentMoveIndex(newIndex);
    // Clear previous move analysis when navigating
    setMoveAnalysis(null);

    // Clear arrows if going to starting position
    if (newIndex === 0) {
      setMoveArrows([]);
    }

    // Trigger analysis if auto-analysis is enabled and not at starting position
    if (gameId && newIndex > 0 && autoAnalysisEnabled) {
      setAnalyzingMove(newIndex);
      setMoveAnalysis(null);
      try {
        moveAnalysisMutation.mutate({ gameId, moveIndex: newIndex });
      } catch (error) {
        console.error("Error triggering move analysis:", error);
        setAnalyzingMove(null);
      }
    }
  };

  const handleMoveClick = async (moveIndex) => {
    // Navigate to the move - analysis will be triggered automatically by goToMove
    goToMove(moveIndex);
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

    // Restore main game arrows
    const arrows = [];
    if (currentMoveIndex > 0 && moves[currentMoveIndex - 1]) {
      const currentMove = moves[currentMoveIndex - 1];
      arrows.push([currentMove.from, currentMove.to, "rgb(255, 170, 0)"]);
    }
    setMoveArrows(arrows);
  };

  const goToVariationMove = (variationMoveIdx) => {
    if (!variationAnalysis || !variationStartFen) return;

    setVariationMoveIndex(
      Math.max(0, Math.min(variationMoveIdx, variationAnalysis.length))
    );

    if (variationMoveIdx === 0) {
      setCurrentPosition(variationStartFen);
      setMoveArrows([]); // Clear arrows at start of variation
    } else {
      const variationMove = variationAnalysis[variationMoveIdx - 1];
      if (variationMove) {
        setCurrentPosition(variationMove.fen);

        // Add arrow for variation move
        // Note: This would require the variation analysis to include move details
        // For now, we'll clear arrows during variation exploration
        setMoveArrows([]);
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
                arrows={moveArrows}
                customSquareStyles={{
                  ...(currentMoveIndex > 0 && moves[currentMoveIndex - 1]
                    ? {
                        [moves[currentMoveIndex - 1].from]: {
                          backgroundColor: "rgba(255, 255, 0, 0.4)",
                        },
                        [moves[currentMoveIndex - 1].to]: {
                          backgroundColor: "rgba(255, 255, 0, 0.4)",
                        },
                      }
                    : {}),
                }}
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
                <div className="mb-5">
                  <div className="text-3xl font-bold mb-2 text-center">
                    <span
                      className={`${
                        typeof moveAnalysis.eval === "string" &&
                        moveAnalysis.eval.includes("#")
                          ? "text-red-600 dark:text-red-400" // Mate scores
                          : moveAnalysis.eval > 0
                          ? "text-green-600 dark:text-green-400"
                          : moveAnalysis.eval < 0
                          ? "text-red-600 dark:text-red-400"
                          : "text-gray-600 dark:text-gray-400"
                      }`}
                    >
                      {typeof moveAnalysis.eval === "string" &&
                      moveAnalysis.eval.includes("#")
                        ? moveAnalysis.eval // Mate notation
                        : `${moveAnalysis.eval > 0 ? "+" : ""}${
                            typeof moveAnalysis.eval === "number"
                              ? moveAnalysis.eval.toFixed(2)
                              : moveAnalysis.eval
                          }`}
                    </span>
                  </div>
                  <div className="text-sm text-muted text-center">
                    {typeof moveAnalysis.eval === "string" &&
                    moveAnalysis.eval.includes("#")
                      ? moveAnalysis.eval.includes("+")
                        ? "White checkmates"
                        : "Black checkmates"
                      : typeof moveAnalysis.eval === "number"
                      ? moveAnalysis.eval > 1
                        ? "White is winning"
                        : moveAnalysis.eval > 0.5
                        ? "White is better"
                        : moveAnalysis.eval > -0.5
                        ? "Equal position"
                        : moveAnalysis.eval > -1
                        ? "Black is better"
                        : "Black is winning"
                      : "Position evaluated"}
                  </div>
                </div>
              )}

              {/* Engine Analysis Variations Section */}
              {moveAnalysis?.variations &&
                moveAnalysis.variations.length > 0 && (
                  <div>
                    <h4 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
                      Top 3 Engine Lines:
                    </h4>
                    {moveAnalysis.variations
                      .slice(0, 3)
                      .map((variation, index) => (
                        <div
                          key={index}
                          className="p-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md mb-2 font-mono text-sm cursor-pointer transition-all duration-200 hover:bg-gray-100 dark:hover:bg-gray-700 hover:border-blue-300 dark:hover:border-blue-600"
                          onClick={() =>
                            handleVariationExplore(variation, currentMoveIndex)
                          }
                          title="Click to explore this variation"
                        >
                          <div className="font-semibold text-gray-700 dark:text-gray-300 mb-1">
                            Line {index + 1}:
                          </div>
                          <div className="text-gray-600 dark:text-gray-400">
                            {variation && variation.length > 80
                              ? variation.substring(0, 80) + "..."
                              : variation || "No moves available"}
                          </div>
                        </div>
                      ))}
                  </div>
                )}

              {/* Debug section - remove after fixing */}
              {moveAnalysis && (
                <div className="mt-3 p-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded text-xs">
                  <div>
                    <strong>Analysis Info:</strong>
                  </div>
                  <div>Eval: {JSON.stringify(moveAnalysis.eval)}</div>
                  <div>
                    Variations count: {moveAnalysis.variations?.length || 0}
                  </div>
                  <div>
                    Source:{" "}
                    {moveAnalysis.explanation?.includes("Basic analysis")
                      ? "Fallback Analysis"
                      : "Lichess Engine"}
                  </div>
                </div>
              )}

              {!moveAnalysis && currentMoveIndex > 0 && autoAnalysisEnabled && (
                <div className="text-center text-muted py-10">
                  <BarChart3 size={32} className="mx-auto mb-3 opacity-30" />
                  <div>Click on a move to see engine analysis</div>
                </div>
              )}

              {!autoAnalysisEnabled && (
                <div className="text-center text-muted py-10">
                  <BarChart3 size={32} className="mx-auto mb-3 opacity-30" />
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
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <div className="text-blue-800 dark:text-blue-200 leading-relaxed">
                    {moveAnalysis.explanation}
                  </div>
                  {/* Show additional info if this is a fallback analysis */}
                  {moveAnalysis.explanation &&
                    moveAnalysis.explanation.includes("Basic analysis") && (
                      <div className="mt-2 text-xs text-blue-600 dark:text-blue-300 italic">
                        💡 This position uses basic evaluation as cloud analysis
                        is unavailable
                      </div>
                    )}
                </div>
              )}

              {autoAIAnalysisEnabled &&
                !moveAnalysis?.explanation &&
                currentMoveIndex > 0 && (
                  <div className="text-center text-muted py-10">
                    <Brain size={32} className="mx-auto mb-3 opacity-30" />
                    <div>Click on a move to see AI explanation</div>
                  </div>
                )}

              {!autoAIAnalysisEnabled && (
                <div className="text-center text-muted py-10">
                  <Brain size={32} className="mx-auto mb-3 opacity-30" />
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
