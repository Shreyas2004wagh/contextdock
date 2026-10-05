import assert from "node:assert/strict";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryMarkdown } from "../src/MemoryMarkdown";

const render = (text: string) => renderToStaticMarkup(<MemoryMarkdown>{text}</MemoryMarkdown>);

test("renders brief headings, emphasis, lists, and code", () => {
  const html = render("# Morning Brief\n\n**Decision:** retry safely.\n\n- `src/retry.ts`\n- Tests\n\n1. Fix the race\n2. Rerun tests\n\n```ts\nconst retries = 3;\n```");
  assert.match(html, /<h3>Morning Brief<\/h3>/);
  assert.match(html, /<strong>Decision:<\/strong>/);
  assert.match(html, /<ul>/);
  assert.match(html, /<ol>/);
  assert.match(html, /<code>src\/retry.ts<\/code>/);
  assert.match(html, /<pre><code class="language-ts">/);
  assert.doesNotMatch(html, /\*\*Decision/);
});

test("supports GFM tables and read-only task lists", () => {
  const html = render("| File | Status |\n| --- | --- |\n| retry.ts | Ready |\n\n- [x] Review\n- [ ] Ship");
  assert.match(html, /aria-label="Answer table"/);
  assert.match(html, /<th>File<\/th>/);
  assert.match(html, /type="checkbox"/);
  assert.match(html, /disabled=""/);
});

test("rejects active HTML, unsafe links, and tracking images", () => {
  const html = render('<script>alert(1)</script>\n\n<iframe src="https://example.com"></iframe>\n\n[bad](javascript:alert%281%29)\n\n![Memory diagram](https://example.com/tracker.png)');
  assert.doesNotMatch(html, /<script|<iframe|<img|javascript:|tracker\.png/);
  assert.match(html, /Memory diagram/);
});

test("opens safe source links without opener access", () => {
  const html = render("[Source](https://example.com/source)");
  assert.match(html, /href="https:\/\/example.com\/source"/);
  assert.match(html, /target="_blank" rel="noopener noreferrer"/);
});
