import { Link } from "react-router-dom";
import { Upload, List, Info } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const HomePage = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div>

      <div className="card">
        <h1>
          <span style={{ marginRight: "10px" }}>♟️</span>
          Chess Game Analysis
        </h1>
        <p>
          Analyze your chess games with engine evaluation and AI explanations.
        </p>
      </div>

      <div className="card">
        <h2>🚀 Upload PGN</h2>
        <div
          style={{
            display: "flex",
            gap: "15px",
            flexWrap: "wrap",
            marginTop: "15px",
            justifyContent: "center",
          }}
        >
          <Link
            to="/upload"
            className="btn btn-primary btn-with-icon"
            style={{ fontSize: "18px", padding: "12px 24px" }}
          >
            <Upload size={20} />
            Paste PGN
          </Link>
          <Link
            to="/games"
            className="btn btn-secondary btn-with-icon"
            style={{ fontSize: "18px", padding: "12px 24px" }}
          >
            <List size={20} />
            Browse Games
          </Link>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
