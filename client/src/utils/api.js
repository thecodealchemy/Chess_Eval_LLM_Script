import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

console.log("API Base URL configured as:", API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Auth token management
let authToken = null;

const setAuthToken = (token) => {
  authToken = token;
  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
};

// Games API
export const gamesApi = {
  // Auth methods
  setAuthToken,

  googleAuth: async (token) => {
    const response = await api.post("/auth/google", { token });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get("/auth/me");
    return response.data;
  },

  uploadPGN: async (title, pgnContent) => {
    const response = await api.post("/games/upload", {
      title,
      pgn_content: pgnContent,
    });
    return response.data;
  },

  // New endpoint for uploading PGN string directly
  uploadPGNString: async (pgnContent) => {
    const response = await api.post("/upload_pgn", {
      pgn: pgnContent,
    });
    return response.data;
  },

  getGames: async (skip = 0, limit = 10) => {
    const response = await api.get("/games", {
      params: { skip, limit },
    });
    return response.data;
  },

  getGame: async (gameId) => {
    const response = await api.get(`/games/${gameId}`);
    return response.data;
  },

  analyzeGame: async (gameId, useLLM = false) => {
    const response = await api.post(`/games/${gameId}/analyze`, {
      game_id: gameId,
      use_llm: useLLM,
    });
    return response.data;
  },

  // New endpoint for limited analysis (current + next 2 positions)
  analyzeLimitedPositions: async (gameId, startMove, useLLM = false) => {
    const response = await api.post(`/games/${gameId}/analyze_limited`, {
      start_move: startMove,
      use_llm: useLLM,
    });
    return response.data;
  },

  getGameAnalysis: async (gameId) => {
    const response = await api.get(`/games/${gameId}/analysis`);
    return response.data;
  },

  deleteGame: async (gameId) => {
    const response = await api.delete(`/games/${gameId}`);
    return response.data;
  },

  // New endpoint for analyzing specific moves
  analyzeMove: async (gameId, moveIndex) => {
    const response = await api.post("/analyse_move", {
      game_id: gameId,
      move_index: moveIndex,
    });
    return response.data;
  },

  // New endpoint for exploring variations
  exploreVariation: async (startFen, variationMoves) => {
    const response = await api.post("/explore_variation", {
      start_fen: startFen,
      variation_moves: variationMoves,
    });
    return response.data;
  },

  // Export annotated PGN
  exportAnnotatedPGN: async (gameId) => {
    const response = await api.get(`/games/${gameId}/export`);
    return response.data;
  },
};

export default api;
