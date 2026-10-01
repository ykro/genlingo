/**
 * Genlingo mark: a vermilion "G" whose crossbar ends in a speech-bubble tail (language), with
 * a cobalt stone inside the curve (David's sling). Vector redraw of design/logo.jpg.
 */
export function LogoMark({ size = 40, title }: { size?: number; title?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
    >
      <path d="M79 27 A35 35 0 1 0 85 58" fill="none" stroke="var(--david)" strokeWidth="19" />
      <path d="M52 47 H94 V82 L76 62 H52 Z" fill="var(--david)" />
      <circle cx="43" cy="52" r="9.5" fill="var(--goliath)" />
    </svg>
  );
}

export function Wordmark({ className = "" }: { className?: string }) {
  return <span className={`display ${className}`} style={{ textTransform: "uppercase", letterSpacing: "0.02em" }}>Genlingo</span>;
}
