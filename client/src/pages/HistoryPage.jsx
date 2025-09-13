import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { gamesApi } from "../utils/api";
import {
  Eye,
  Trash2,
  Calendar,
  Users,
  Clock,
  Trophy,
  BarChart3,
  Search,
  Filter,
  History,
} from "lucide-react";
import { useState } from "react";

const HistoryPage = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterResult, setFilterResult] = useState("all");
  const queryClient = useQueryClient();

  const {
    data: games,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["games"],
    queryFn: () => gamesApi.getGames(0, 50), // Get more games for history
  });

  const deleteMutation = useMutation({
    mutationFn: gamesApi.deleteGame,
    onSuccess: () => {
      queryClient.invalidateQueries(["games"]);
    },
  });

  const handleDelete = (gameId, gameTitle) => {
    if (window.confirm(`Are you sure you want to delete "${gameTitle}"?`)) {
      deleteMutation.mutate(gameId);
    }
  };

  // Filter games based on search and result filter
  const filteredGames = games?.filter((game) => {
    const matchesSearch =
      !searchTerm ||
      game.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      game.white_player?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      game.black_player?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      game.event?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter =
      filterResult === "all" || game.result === filterResult;

    return matchesSearch && matchesFilter;
  });

  const getResultIcon = (result) => {
    switch (result) {
      case "1-0":
        return "🏆";
      case "0-1":
        return "🥈";
      case "1/2-1/2":
        return "🤝";
      default:
        return "❓";
    }
  };

  const getResultColor = (result) => {
    switch (result) {
      case "1-0":
        return "#28a745";
      case "0-1":
        return "#dc3545";
      case "1/2-1/2":
        return "#ffc107";
      default:
        return "#6c757d";
    }
  };

  if (isLoading) {
    return (
      <div className="loading">
        <History size={32} style={{ marginBottom: "10px" }} />
        <div>Loading game history...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        Error loading game history:{" "}
        {error.response?.data?.detail || error.message}
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="card">
        <div
          style={{
            display: "flex",
            alignItems: "center",
            marginBottom: "10px",
          }}
        >
          <History
            size={28}
            style={{ marginRight: "12px", color: "#007bff" }}
          />
          <div>
            <h1 style={{ margin: 0 }}>Game History</h1>
            <p style={{ margin: "5px 0 0 0", color: "#666" }}>
              All your analyzed chess games from MongoDB storage
            </p>
          </div>
        </div>

        {/* Search and Filter Controls */}
        <div
          style={{
            display: "flex",
            gap: "15px",
            marginTop: "20px",
            flexWrap: "wrap",
            alignItems: "center",
          }}
        >
          <div style={{ flex: "1", minWidth: "200px", position: "relative" }}>
            <Search
              size={16}
              style={{
                position: "absolute",
                left: "10px",
                top: "50%",
                transform: "translateY(-50%)",
                color: "#666",
              }}
            />
            <input
              type="text"
              placeholder="Search games, players, events..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-control"
              style={{ paddingLeft: "35px" }}
            />
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Filter size={16} />
            <select
              value={filterResult}
              onChange={(e) => setFilterResult(e.target.value)}
              className="form-control"
              style={{ width: "auto" }}
            >
              <option value="all">All Results</option>
              <option value="1-0">White Wins</option>
              <option value="0-1">Black Wins</option>
              <option value="1/2-1/2">Draws</option>
            </select>
          </div>

          <Link to="/upload" className="btn btn-primary">
            Upload New Game
          </Link>
        </div>

        {/* Statistics */}
        {games && games.length > 0 && (
          <div
            style={{
              marginTop: "20px",
              padding: "15px",
              backgroundColor: "#f8f9fa",
              borderRadius: "6px",
              display: "flex",
              gap: "20px",
              flexWrap: "wrap",
            }}
          >
            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  fontSize: "24px",
                  fontWeight: "bold",
                  color: "#007bff",
                }}
              >
                {games.length}
              </div>
              <div style={{ fontSize: "12px", color: "#666" }}>Total Games</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  fontSize: "24px",
                  fontWeight: "bold",
                  color: "#28a745",
                }}
              >
                {games.filter((g) => g.result === "1-0").length}
              </div>
              <div style={{ fontSize: "12px", color: "#666" }}>White Wins</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  fontSize: "24px",
                  fontWeight: "bold",
                  color: "#dc3545",
                }}
              >
                {games.filter((g) => g.result === "0-1").length}
              </div>
              <div style={{ fontSize: "12px", color: "#666" }}>Black Wins</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  fontSize: "24px",
                  fontWeight: "bold",
                  color: "#ffc107",
                }}
              >
                {games.filter((g) => g.result === "1/2-1/2").length}
              </div>
              <div style={{ fontSize: "12px", color: "#666" }}>Draws</div>
            </div>
          </div>
        )}
      </div>

      {/* Games List */}
      {!filteredGames || filteredGames.length === 0 ? (
        <div className="card">
          <div style={{ textAlign: "center", padding: "40px" }}>
            {searchTerm || filterResult !== "all" ? (
              <>
                <p
                  style={{
                    fontSize: "18px",
                    color: "#666",
                    marginBottom: "20px",
                  }}
                >
                  No games match your search criteria.
                </p>
                <button
                  onClick={() => {
                    setSearchTerm("");
                    setFilterResult("all");
                  }}
                  className="btn btn-secondary"
                >
                  Clear Filters
                </button>
              </>
            ) : (
              <>
                <p
                  style={{
                    fontSize: "18px",
                    color: "#666",
                    marginBottom: "20px",
                  }}
                >
                  No games in your history yet.
                </p>
                <Link to="/upload" className="btn btn-primary">
                  Upload Your First Game
                </Link>
              </>
            )}
          </div>
        </div>
      ) : (
        <div className="card">
          <div
            style={{ marginBottom: "15px", color: "#666", fontSize: "14px" }}
          >
            Showing {filteredGames.length} of {games.length} games
          </div>

          <div
            className="games-grid"
            style={{
              display: "grid",
              gap: "15px",
              gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))",
            }}
          >
            {filteredGames.map((game) => (
              <div
                key={game.id}
                className="game-card"
                style={{
                  border: "1px solid #dee2e6",
                  borderRadius: "8px",
                  padding: "15px",
                  backgroundColor: "white",
                  transition: "all 0.2s ease",
                  cursor: "pointer",
                }}
                onMouseEnter={(e) => {
                  e.target.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
                  e.target.style.transform = "translateY(-2px)";
                }}
                onMouseLeave={(e) => {
                  e.target.style.boxShadow = "none";
                  e.target.style.transform = "translateY(0)";
                }}
              >
                {/* Game Header */}
                <div style={{ marginBottom: "12px" }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <h3
                      style={{ margin: 0, fontSize: "16px", fontWeight: "600" }}
                    >
                      {game.title || `Game ${game.id.slice(-6)}`}
                    </h3>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        padding: "4px 8px",
                        borderRadius: "12px",
                        backgroundColor: getResultColor(game.result) + "20",
                        color: getResultColor(game.result),
                        fontSize: "12px",
                        fontWeight: "600",
                      }}
                    >
                      {getResultIcon(game.result)} {game.result || "Unknown"}
                    </div>
                  </div>

                  {game.event && (
                    <div
                      style={{
                        fontSize: "13px",
                        color: "#666",
                        marginTop: "4px",
                      }}
                    >
                      📍 {game.event}
                    </div>
                  )}
                </div>

                {/* Players */}
                <div style={{ marginBottom: "12px" }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      marginBottom: "4px",
                    }}
                  >
                    <Users
                      size={14}
                      style={{ marginRight: "6px", color: "#666" }}
                    />
                    <span style={{ fontSize: "14px" }}>
                      <strong>{game.white_player || "Unknown"}</strong>
                      <span style={{ color: "#666", margin: "0 8px" }}>vs</span>
                      <strong>{game.black_player || "Unknown"}</strong>
                    </span>
                  </div>
                </div>

                {/* Game Info */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    fontSize: "12px",
                    color: "#666",
                    marginBottom: "15px",
                  }}
                >
                  <div>
                    {game.date_played && (
                      <div style={{ display: "flex", alignItems: "center" }}>
                        <Calendar size={12} style={{ marginRight: "4px" }} />
                        {game.date_played}
                      </div>
                    )}
                  </div>
                  <div>
                    {game.move_count && (
                      <div style={{ display: "flex", alignItems: "center" }}>
                        <BarChart3 size={12} style={{ marginRight: "4px" }} />
                        {game.move_count} moves
                      </div>
                    )}
                  </div>
                  <div>
                    <Clock size={12} style={{ marginRight: "4px" }} />
                    {new Date(game.upload_date).toLocaleDateString()}
                  </div>
                </div>

                {/* Actions */}
                <div
                  style={{
                    display: "flex",
                    gap: "8px",
                    justifyContent: "flex-end",
                    borderTop: "1px solid #f1f3f4",
                    paddingTop: "12px",
                  }}
                >
                  <Link
                    to={`/games/${game.id}`}
                    className="btn btn-primary"
                    style={{
                      padding: "6px 12px",
                      fontSize: "12px",
                      display: "flex",
                      alignItems: "center",
                    }}
                  >
                    <Eye size={14} style={{ marginRight: "4px" }} />
                    Analyze
                  </Link>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(game.id, game.title);
                    }}
                    className="btn btn-danger"
                    style={{
                      padding: "6px 12px",
                      fontSize: "12px",
                      display: "flex",
                      alignItems: "center",
                    }}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {deleteMutation.error && (
        <div className="error">
          Error deleting game:{" "}
          {deleteMutation.error.response?.data?.detail ||
            deleteMutation.error.message}
        </div>
      )}
    </div>
  );
};

export default HistoryPage;
