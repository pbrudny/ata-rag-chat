interface ConfidenceBadgeProps {
  confidence: number;
  answered: boolean;
}

export function ConfidenceBadge({ confidence, answered }: ConfidenceBadgeProps) {
  if (!answered) return null;

  const percent = Math.round(confidence * 100);
  const color =
    confidence >= 0.75
      ? "text-green-700"
      : confidence >= 0.55
        ? "text-yellow-700"
        : "text-red-700";

  return <p className={`mt-1 text-xs ${color}`}>Confidence: {percent}%</p>;
}
