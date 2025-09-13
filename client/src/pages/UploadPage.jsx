import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { gamesApi } from "../utils/api";
import {
  Upload,
  FileText,
  Clipboard,
  ChevronRight,
  Info,
  LogIn,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import GoogleLoginButton from "../components/GoogleLoginButton";

const UploadPage = () => {
  const [pgnContent, setPgnContent] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const { isAuthenticated, user } = useAuth();

  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Use the new upload_pgn endpoint
  const uploadMutation = useMutation({
    mutationFn: (pgnContent) => gamesApi.uploadPGNString(pgnContent),
    onSuccess: (data) => {
      queryClient.invalidateQueries(["games"]);
      // Redirect to analysis page for the uploaded game
      navigate(`/games/${data.game_id}`);
    },
    onError: (error) => {
      console.error("Upload error:", error);
      setIsProcessing(false);
    },
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!pgnContent.trim()) return;

    setIsProcessing(true);

    // Clean up Chess.com PGN format
    const cleanedPGN = cleanChessDotComPGN(pgnContent.trim());

    uploadMutation.mutate(cleanedPGN);
  };

  // Function to clean and optimize Chess.com PGN format
  const cleanChessDotComPGN = (pgn) => {
    // Remove excessive whitespace and normalize line breaks
    let cleaned = pgn
      .replace(/\]\s*\[/g, "]\n[") // Ensure headers are on separate lines
      .replace(/\n\s*\n/g, "\n") // Remove excessive blank lines
      .trim();

    // Ensure proper header format for Chess.com PGNs
    if (!cleaned.includes("[Event")) {
      // If no headers, add basic ones
      const timestamp = new Date()
        .toISOString()
        .split("T")[0]
        .replace(/-/g, ".");
      cleaned = `[Event "Chess.com Game"]
[Site "Chess.com"]
[Date "${timestamp}"]
[White "Player1"]
[Black "Player2"]
[Result "*"]

${cleaned}`;
    }

    // Fix common Chess.com PGN issues
    cleaned = cleaned
      .replace(/\{[^}]*\}/g, "") // Remove comments in curly braces
      .replace(/\s*\n\s*/g, "\n") // Clean line breaks but preserve structure
      .replace(/([\]\s]+)(1\.)/, "$1\n\n$2"); // Ensure proper spacing before moves

    return cleaned;
  };

  const handlePaste = () => {
    navigator.clipboard
      .readText()
      .then((text) => {
        setPgnContent(text);
      })
      .catch((err) => {
        console.error("Failed to read clipboard contents: ", err);
      });
  };

  const sampleChessDotComPGN = `[Event "Live Chess"]
[Site "Chess.com"]
[Date "2024.01.15"]
[Round "-"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]
[WhiteElo "1500"]
[BlackElo "1450"]
[TimeControl "600"]
[EndTime "10:30:45 PST"]
[Termination "Player1 won by checkmate"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7 1-0`;

  return (
    <div>
      {!isAuthenticated && (
        <div
          className="card"
          style={{ backgroundColor: "#fff3cd", borderColor: "#ffeaa7" }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              marginBottom: "12px",
            }}
          >
            <Info size={20} style={{ marginRight: "8px", color: "#856404" }} />
            <h3 style={{ margin: 0, color: "#856404" }}>Anonymous Upload</h3>
          </div>
          <p style={{ margin: "0 0 12px 0", color: "#856404" }}>
            You're uploading anonymously. Your game will be saved to the
            database but won't be associated with your account. Sign in to keep
            track of your games and manage them later.
          </p>
          <button
            onClick={() => setShowLoginModal(true)}
            className="btn btn-primary"
            style={{ display: "flex", alignItems: "center" }}
          >
            <LogIn size={16} style={{ marginRight: "6px" }} />
            Sign In to Save to Your Account
          </button>
        </div>
      )}

      <div className="card">
        <h1>
          <FileText
            size={24}
            style={{ marginRight: "8px", verticalAlign: "middle" }}
          />
          Upload Chess Game
        </h1>
        <p>
          Paste your PGN from Chess.com or any other platform. The system will
          automatically parse the game data and redirect you to the analysis
          page.
        </p>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "8px",
              }}
            >
              <label
                htmlFor="pgn-content"
                style={{ fontSize: "16px", fontWeight: "600" }}
              >
                Chess.com PGN Content
              </label>
              <button
                type="button"
                onClick={handlePaste}
                className="btn btn-secondary"
                style={{ padding: "4px 8px", fontSize: "12px" }}
              >
                <Clipboard size={14} style={{ marginRight: "4px" }} />
                Paste from Clipboard
              </button>
            </div>

            <textarea
              id="pgn-content"
              className="form-control"
              rows="20"
              value={pgnContent}
              onChange={(e) => setPgnContent(e.target.value)}
              placeholder={`Paste your Chess.com PGN here...\n\nExample format:\n${sampleChessDotComPGN}`}
              style={{
                fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                fontSize: "13px",
                lineHeight: "1.4",
              }}
              required
            />
          </div>

          <div
            style={{
              marginBottom: "20px",
              padding: "12px",
              backgroundColor: "#e3f2fd",
              borderRadius: "6px",
              border: "1px solid #90caf9",
            }}
          >
            <h4
              style={{
                margin: "0 0 8px 0",
                color: "#1565c0",
                fontSize: "14px",
              }}
            >
              💡 Chess.com PGN Tips:
            </h4>
            <ul
              style={{
                margin: 0,
                paddingLeft: "20px",
                fontSize: "13px",
                color: "#1976d2",
              }}
            >
              <li>Copy the entire PGN from your Chess.com game page</li>
              <li>
                The system automatically extracts player names, ratings, and
                game details
              </li>
              <li>Time controls and termination reasons are preserved</li>
              <li>Comments and annotations are cleaned up automatically</li>
            </ul>
          </div>

          {uploadMutation.error && (
            <div className="error">
              Error uploading game:{" "}
              {uploadMutation.error.response?.data?.detail ||
                uploadMutation.error.message}
            </div>
          )}

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={
                uploadMutation.isPending || !pgnContent.trim() || isProcessing
              }
              style={{ display: "flex", alignItems: "center" }}
            >
              <Upload size={16} style={{ marginRight: "8px" }} />
              {uploadMutation.isPending || isProcessing
                ? "Processing..."
                : "Upload & Analyze Game"}
              <ChevronRight size={16} style={{ marginLeft: "8px" }} />
            </button>

            {pgnContent.trim() && (
              <span style={{ color: "#28a745", fontSize: "14px" }}>
                ✓ Ready to upload ({pgnContent.trim().split("\n").length} lines)
              </span>
            )}
          </div>
        </form>
      </div>

      <div className="card">
        <h3>How it works:</h3>
        <ol style={{ lineHeight: "1.6" }}>
          <li>
            <strong>Paste PGN:</strong> Copy your game PGN from Chess.com
          </li>
          <li>
            <strong>Auto-parse:</strong> System extracts game metadata and moves
          </li>
          <li>
            <strong>Instant redirect:</strong> Automatically opens the analysis
            page
          </li>
          <li>
            <strong>Click moves:</strong> Click any move to get AI analysis with
            engine evaluation
          </li>
        </ol>
      </div>

      {showLoginModal && (
        <GoogleLoginButton onClose={() => setShowLoginModal(false)} />
      )}
    </div>
  );
};

export default UploadPage;
