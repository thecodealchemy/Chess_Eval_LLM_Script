import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useState } from "react";
import { gamesApi } from "../utils/api";
import { Eye, Trash2, Calendar, Users, Info, LogIn } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import GoogleLoginButton from "../components/GoogleLoginButton";

const GameListPage = () => {
  const queryClient = useQueryClient();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const { isAuthenticated, user } = useAuth();

  const {
    data: games,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["games"],
    queryFn: () => gamesApi.getGames(),
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

  if (isLoading) {
    return <div className="loading">Loading games...</div>;
  }

  if (error) {
    return (
      <div className="error">
        Error loading games: {error.response?.data?.detail || error.message}
      </div>
    );
  }

  return (
    <div>
      {!isAuthenticated && (
        <div className="card info-card">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              marginBottom: "12px",
            }}
          >
            <Info size={20} className="mr-2" />
            <h3 style={{ margin: 0 }}>Viewing All Games</h3>
          </div>
          <p style={{ margin: "0 0 12px 0" }}>
            You're viewing all games from all users. Sign in to see only your
            games and manage them.
          </p>
          <button
            onClick={() => setShowLoginModal(true)}
            className="btn btn-primary"
            style={{ display: "flex", alignItems: "center" }}
          >
            <LogIn size={16} style={{ marginRight: "6px" }} />
            Sign In to Manage Your Games
          </button>
        </div>
      )}

      <div className="card">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h1>{isAuthenticated ? "Your Chess Games" : "All Chess Games"}</h1>
          <Link to="/" className="btn btn-primary">
            Upload New Game
          </Link>
        </div>
        <p>
          {isAuthenticated
            ? "Manage and analyze your uploaded chess games."
            : "Browse and analyze chess games from all users."}
        </p>
      </div>

      {games && games.length === 0 ? (
        <div className="card">
          <div style={{ textAlign: "center", padding: "40px" }}>
            <p
              className="text-muted"
              style={{ fontSize: "18px", marginBottom: "20px" }}
            >
              No games uploaded yet.
            </p>
            <Link to="/" className="btn btn-primary">
              Upload Your First Game
            </Link>
          </div>
        </div>
      ) : (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Players</th>
                <th>Result</th>
                <th>Date</th>
                <th>Moves</th>
                <th>Uploaded</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {games?.map((game) => (
                <tr key={game.id}>
                  <td>
                    <strong>{game.title}</strong>
                    {game.event && (
                      <div className="text-muted" style={{ fontSize: "12px" }}>
                        {game.event}
                      </div>
                    )}
                  </td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center" }}>
                      <Users size={14} style={{ marginRight: "4px" }} />
                      <div>
                        <div>{game.white_player || "Unknown"}</div>
                        <div style={{ fontSize: "12px", color: "#666" }}>
                          vs {game.black_player || "Unknown"}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: "12px",
                        fontSize: "12px",
                        backgroundColor:
                          game.result === "1-0"
                            ? "#d4edda"
                            : game.result === "0-1"
                            ? "#f8d7da"
                            : game.result === "1/2-1/2"
                            ? "#fff3cd"
                            : "#e2e3e5",
                        color:
                          game.result === "1-0"
                            ? "#155724"
                            : game.result === "0-1"
                            ? "#721c24"
                            : game.result === "1/2-1/2"
                            ? "#856404"
                            : "#6c757d",
                      }}
                    >
                      {game.result || "Unknown"}
                    </span>
                  </td>
                  <td>
                    {game.date_played ? (
                      <div style={{ display: "flex", alignItems: "center" }}>
                        <Calendar size={14} style={{ marginRight: "4px" }} />
                        {game.date_played}
                      </div>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td>{game.move_count || "-"}</td>
                  <td>{new Date(game.upload_date).toLocaleDateString()}</td>
                  <td>
                    <div style={{ display: "flex", gap: "8px" }}>
                      <Link
                        to={`/games/${game.id}`}
                        className="btn btn-primary"
                        style={{ padding: "4px 8px", fontSize: "12px" }}
                      >
                        <Eye size={14} />
                      </Link>
                      {isAuthenticated && (
                        <button
                          onClick={() => handleDelete(game.id, game.title)}
                          className="btn btn-danger"
                          style={{ padding: "4px 8px", fontSize: "12px" }}
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {deleteMutation.error && (
        <div className="error">
          Error deleting game:{" "}
          {deleteMutation.error.response?.data?.detail ||
            deleteMutation.error.message}
        </div>
      )}

      {showLoginModal && (
        <GoogleLoginButton onClose={() => setShowLoginModal(false)} />
      )}
    </div>
  );
};

export default GameListPage;
