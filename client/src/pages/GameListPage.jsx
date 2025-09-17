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
    return (
      <div className="loading">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
        <div>Loading games...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="error">
          <div className="flex items-center mb-2">
            <Info size={20} className="mr-2" />
            <strong>Error Loading Games</strong>
          </div>
          <p>{error.response?.data?.detail || error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {isAuthenticated ? "Your Chess Games" : "All Chess Games"}
            </h1>
            <p className="text-muted mt-1">
              {isAuthenticated
                ? "Manage and analyze your uploaded chess games."
                : "Browse and analyze chess games from all users."}
            </p>
          </div>
          <Link to="/" className="btn btn-primary">
            Upload New Game
          </Link>
        </div>
      </div>

      {games && games.length === 0 ? (
        <div className="card">
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🏆</div>
            <p className="text-muted text-lg mb-6">
              No games uploaded yet.
            </p>
            <Link to="/" className="btn btn-primary">
              Upload Your First Game
            </Link>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="games-grid">
            {games?.map((game) => {
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

              const getResultClasses = (result) => {
                switch (result) {
                  case "1-0":
                    return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
                  case "0-1":
                    return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
                  case "1/2-1/2":
                    return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400";
                  default:
                    return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400";
                }
              };

              return (
                <div
                  key={game.id}
                  className="game-card transition-all duration-200 hover:shadow-lg hover:-translate-y-1"
                >
                  {/* Game Header */}
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                      {game.title || `Game ${game.id.slice(-6)}`}
                    </h3>
                    <div
                      className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${getResultClasses(
                        game.result
                      )}`}
                    >
                      <span className="mr-1">{getResultIcon(game.result)}</span>
                      {game.result || "Unknown"}
                    </div>
                  </div>

                  {game.event && (
                    <div className="text-muted text-sm mb-3 flex items-center">
                      <span className="mr-1">📍</span>
                      {game.event}
                    </div>
                  )}

                  {/* Players */}
                  <div className="mb-4">
                    <div className="flex items-center text-sm">
                      <Users size={14} className="text-muted mr-2" />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 dark:text-white">
                          {game.white_player || "Unknown"}
                        </div>
                        <div className="text-muted text-xs">
                          vs {game.black_player || "Unknown"}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Game Info */}
                  <div className="grid grid-cols-2 gap-4 text-xs text-muted mb-4">
                    <div>
                      {game.date_played && (
                        <div className="flex items-center">
                          <Calendar size={12} className="mr-1" />
                          {game.date_played}
                        </div>
                      )}
                    </div>
                    <div>
                      {game.move_count && (
                        <div className="flex items-center">
                          <span className="mr-1">⚡</span>
                          {game.move_count} moves
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="text-xs text-muted mb-4">
                    Uploaded: {new Date(game.upload_date).toLocaleDateString()}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <Link
                      to={`/games/${game.id}`}
                      className="btn btn-primary flex-1 justify-center text-sm py-2"
                    >
                      <Eye size={14} className="mr-1" />
                      Analyze
                    </Link>
                    {isAuthenticated && (
                      <button
                        onClick={() => handleDelete(game.id, game.title)}
                        className="btn btn-danger px-3 py-2"
                        disabled={deleteMutation.isPending}
                        title="Delete game"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {deleteMutation.error && (
        <div className="card">
          <div className="error">
            <div className="flex items-center mb-2">
              <Trash2 size={20} className="mr-2" />
              <strong>Error Deleting Game</strong>
            </div>
            <p>
              {deleteMutation.error.response?.data?.detail ||
                deleteMutation.error.message}
            </p>
          </div>
        </div>
      )}

      {showLoginModal && (
        <GoogleLoginButton onClose={() => setShowLoginModal(false)} />
      )}
    </div>
  );
};

export default GameListPage;
