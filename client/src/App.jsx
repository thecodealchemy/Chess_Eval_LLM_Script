import { Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import Navigation from "./components/Navigation";
import HomePage from "./pages/HomePage";
import GameListPage from "./pages/GameListPage";
import GameDetailPage from "./pages/GameDetailPage";
import HistoryPage from "./pages/HistoryPage";

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <div className="min-h-screen bg-gray-50 dark:bg-dark-bg transition-colors">
          <Navigation />
          <div className="container">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/games" element={<GameListPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/games/:gameId" element={<GameDetailPage />} />
            </Routes>
          </div>
        </div>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
