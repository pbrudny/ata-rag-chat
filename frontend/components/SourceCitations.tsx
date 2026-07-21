import type { ChatSource } from "@/lib/types";

interface SourceCitationsProps {
  sources: ChatSource[];
}

export function SourceCitations({ sources }: SourceCitationsProps) {
  if (sources.length === 0) return null;

  return (
    <ul className="mt-2 space-y-1 border-t border-gray-300 pt-2 text-sm">
      {sources.map((source) => (
        <li key={source.url}>
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-700 underline"
          >
            {source.title ?? source.url}
          </a>
          {source.section && <span className="text-gray-500"> — {source.section}</span>}
        </li>
      ))}
    </ul>
  );
}
