import { useTheme } from "../contexts/ThemeContext";
import { Sun, Moon } from "lucide-react";

const ThemeToggle = ({ className = "" }) => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`btn btn-secondary p-2 ${className}`}
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {isDark ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  );
};

export default ThemeToggle;
