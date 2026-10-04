import { useState } from "react";
import { ArrowDown, ArrowRight, Brain, Check, FileCode2, GitBranch, MessageSquareText, Terminal } from "lucide-react";

const examples = [
  { label: "The handoff", question: "Where did we leave off?", title: "Webhook retries are ready for review.", body: "You added bounded retries and duplicate delivery protection. One timeout test is still blocking the release.", detail: "Keep idempotency keys for 24 hours. Retry failed deliveries three times with exponential backoff.", source: "Session decision", icon: Brain },
  { label: "The files", question: "Which files need my attention?", title: "Start with the delivery handler.", body: "The retry policy lives in retry.ts. The timeout-after-success test points to an idempotency check in delivery.ts.", detail: "src/webhooks/delivery.ts\nsrc/webhooks/retry.ts\ntests/webhooks.test.ts", source: "Changed files", icon: FileCode2 },
  { label: "The next move", question: "What should I tackle next?", title: "Reproduce the timeout race first.", body: "A completed delivery can be retried after a timeout. Verify the idempotency check before changing the retry policy.", detail: "Fix the duplicate-delivery path, rerun the webhook suite, then send the release for review.", source: "Session next steps", icon: GitBranch },
];

export function MemoryPreview() {
  const [selected, setSelected] = useState(0);
  const example = examples[selected];
  const Icon = example.icon;
  return (
    <section className="interactive-preview" id="product-preview" aria-label="Interactive example session">
      <header className="example-toolbar">
        <span><span className="example-logo"><Brain size={17} /></span> Release Atlas <span className="example-slash">/</span><span className="example-space-name">Project memory</span></span>
        <span className="example-label">EXAMPLE SESSION</span>
      </header>
      <div className="example-layout">
        <aside className="example-sidebar">
          <span className="example-eyebrow">SAVED CONTEXT</span>
          <div className="example-session"><Terminal size={17} /><div><strong>Webhook delivery</strong><small>Last coding session</small></div><Check size={14} /></div>
          <div className="example-source"><FileCode2 size={14} /><span>delivery.ts</span></div>
          <div className="example-source"><FileCode2 size={14} /><span>retry.ts</span></div>
          <div className="example-source"><GitBranch size={14} /><span>Release decision</span></div>
          <div className="example-memory"><Brain size={23} /><span>Context preserved<br /><small>Across sessions. Across handoffs.</small></span></div>
        </aside>
        <div className="example-content">
          <div className="example-tabs" role="group" aria-label="Explore the example">
            {examples.map((item, index) => <button key={item.label} aria-pressed={selected === index} onClick={() => setSelected(index)} type="button">{item.label}</button>)}
          </div>
          <div className="example-question"><MessageSquareText size={17} />{example.question}<ArrowDown size={15} /></div>
          <div className="example-answer" key={selected} aria-live="polite">
            <span className="example-answer-label"><Brain size={16} /> CONTEXT RECOVERED</span>
            <h2>{example.title}</h2>
            <p>{example.body}</p>
            <div className="example-detail"><Icon size={16} /><div><span>{example.source}</span><p>{example.detail}</p></div></div>
          </div>
          <a className="example-open" href="#signin">Bring your own context <ArrowRight size={15} /></a>
        </div>
      </div>
      <footer className="example-footer"><span><span className="connection-dot" /> Powered by Cognee memory</span><span>Illustrative example · Your workspace uses live memory</span></footer>
    </section>
  );
}
