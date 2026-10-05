import React from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function MemoryMarkdown({ children }: { children: string }) {
  return (
    <div className="memory-markdown">
      <Markdown
        remarkPlugins={[remarkGfm]}
        skipHtml
        components={{
          h1: ({ children }) => <h3>{children}</h3>,
          h2: ({ children }) => <h3>{children}</h3>,
          a: ({ href, children }) => href
            ? <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
            : <span>{children}</span>,
          // Memory content must not load third-party tracking images.
          img: ({ alt }) => <span>{alt}</span>,
          table: ({ children }) => <div className="markdown-table" tabIndex={0} role="region" aria-label="Answer table"><table>{children}</table></div>,
        }}
      >
        {children}
      </Markdown>
    </div>
  );
}
