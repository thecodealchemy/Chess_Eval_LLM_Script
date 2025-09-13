import { useMemo } from "react";

const EvaluationBar = ({ evaluation, className = "" }) => {
  const { percentage, displayValue } = useMemo(() => {
    if (evaluation === null || evaluation === undefined) {
      return {
        percentage: 50,
        displayValue: "0.0",
      };
    }

    // Clamp evaluation between -10 and +10 for display
    const clampedEval = Math.max(-10, Math.min(10, evaluation));

    // Convert to percentage (0-100%)
    // -10 = 0%, 0 = 50%, +10 = 100%
    const percentage = ((clampedEval + 10) / 20) * 100;

    // Format display value
    const displayValue =
      evaluation > 0 ? `+${evaluation.toFixed(1)}` : evaluation.toFixed(1);

    return { percentage, displayValue };
  }, [evaluation]);

  return (
    <div className={`flex flex-col items-center ${className}`}>
      {/* Evaluation number */}
      <div className="text-sm font-bold mb-2 text-gray-700 dark:text-gray-300 h-5">
        {displayValue}
      </div>

      {/* Evaluation bar */}
      <div className="eval-bar">
        {/* White advantage area (top) */}
        <div
          className="absolute top-0 left-0 right-0 bg-white border-b border-gray-300"
          style={{ height: `${100 - percentage}%` }}
        >
          {percentage > 75 && (
            <div className="absolute bottom-1 left-1/2 transform -translate-x-1/2">
              <span className="text-xs font-bold text-gray-700">W</span>
            </div>
          )}
        </div>

        {/* Black advantage area (bottom) */}
        <div
          className="absolute bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-600"
          style={{ height: `${percentage}%` }}
        >
          {percentage < 25 && (
            <div className="absolute top-1 left-1/2 transform -translate-x-1/2">
              <span className="text-xs font-bold text-white">B</span>
            </div>
          )}
        </div>

        {/* Center line */}
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gray-500 transform -translate-y-1/2" />
      </div>

      {/* Labels */}
      <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">Eval</div>
    </div>
  );
};

export default EvaluationBar;
