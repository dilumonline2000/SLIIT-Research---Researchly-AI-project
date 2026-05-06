"use client";

import { useMemo, useState } from "react";

export interface GraphNode {
  id: string;
  label: string;
  /** Type drives the colour palette: central | primary | secondary | detail */
  type?: "central" | "primary" | "secondary" | "detail";
  /** Backwards-compat: if `color` is set we use it as a flat fallback. */
  color?: string;
  /** Drives radius: ~ 10 + val * 0.55 */
  val: number;
}

export interface GraphLink {
  source: string;
  target: string;
  weight: number;
}

interface SimPos {
  x: number;
  y: number;
}

// ── Palette ──────────────────────────────────────────────────────────────
// Each type gets a 2-stop gradient + a base hex (used for shadows / labels).
const PALETTE = {
  central:   { from: "#a855f7", to: "#6366f1", solid: "#7c3aed", label: "Central" },
  primary:   { from: "#3b82f6", to: "#06b6d4", solid: "#2563eb", label: "Primary" },
  secondary: { from: "#10b981", to: "#06b6d4", solid: "#059669", label: "Secondary" },
  detail:    { from: "#f59e0b", to: "#f97316", solid: "#ea580c", label: "Detail" },
} as const;

export type NodeType = keyof typeof PALETTE;

function paletteFor(node: GraphNode): typeof PALETTE.central {
  return PALETTE[(node.type ?? "detail") as NodeType] ?? PALETTE.detail;
}

// ── Force layout ─────────────────────────────────────────────────────────
function runForceLayout(
  nodes: GraphNode[],
  links: GraphLink[],
  width: number,
  height: number,
): Map<string, SimPos> {
  const cx = width / 2;
  const cy = height / 2;
  const positions = new Map<string, { x: number; y: number; vx: number; vy: number }>();

  nodes.forEach((n, i) => {
    const angle = (i / Math.max(1, nodes.length)) * 2 * Math.PI;
    const r = Math.min(width, height) * 0.28;
    positions.set(n.id, {
      x: cx + Math.cos(angle) * r * (0.6 + Math.random() * 0.4),
      y: cy + Math.sin(angle) * r * (0.6 + Math.random() * 0.4),
      vx: 0,
      vy: 0,
    });
  });

  const ITERATIONS = 280;
  const REPULSION = 2400;
  const DECAY = 0.86;

  for (let t = 0; t < ITERATIONS; t++) {
    const alpha = 0.4 * Math.pow(0.985, t);

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = positions.get(nodes[i].id)!;
        const b = positions.get(nodes[j].id)!;
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const d2 = dx * dx + dy * dy + 0.5;
        const force = (REPULSION * alpha) / d2;
        a.vx += dx * force;
        a.vy += dy * force;
        b.vx -= dx * force;
        b.vy -= dy * force;
      }
    }

    for (const link of links) {
      const s = positions.get(link.source);
      const t2 = positions.get(link.target);
      if (!s || !t2) continue;
      const dx = t2.x - s.x;
      const dy = t2.y - s.y;
      const d = Math.sqrt(dx * dx + dy * dy) + 0.1;
      const sNode = nodes.find((n) => n.id === link.source);
      const tNode = nodes.find((n) => n.id === link.target);
      const restLen = 80 + (sNode?.val ?? 6) + (tNode?.val ?? 6);
      const force = (d - restLen) * 0.06 * alpha;
      const fx = (dx / d) * force;
      const fy = (dy / d) * force;
      s.vx += fx;
      s.vy += fy;
      t2.vx -= fx;
      t2.vy -= fy;
    }

    for (const [, p] of positions) {
      p.vx += (cx - p.x) * 0.025 * alpha;
      p.vy += (cy - p.y) * 0.025 * alpha;
      p.vx *= DECAY;
      p.vy *= DECAY;
      p.x += p.vx;
      p.y += p.vy;
    }
  }

  const PAD = 80;
  const xs = [...positions.values()].map((p) => p.x);
  const ys = [...positions.values()].map((p) => p.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const scaleX = (width - PAD * 2) / Math.max(1, maxX - minX);
  const scaleY = (height - PAD * 2) / Math.max(1, maxY - minY);
  const scale = Math.min(scaleX, scaleY, 1.8);

  const result = new Map<string, SimPos>();
  for (const [id, p] of positions) {
    result.set(id, {
      x: PAD + (p.x - minX) * scale + ((width - PAD * 2) - (maxX - minX) * scale) / 2,
      y: PAD + (p.y - minY) * scale + ((height - PAD * 2) - (maxY - minY) * scale) / 2,
    });
  }
  return result;
}

interface MindMapGraphProps {
  nodes: GraphNode[];
  links: GraphLink[];
  width: number;
  height: number;
}

export function MindMapGraph({ nodes, links, width, height }: MindMapGraphProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const positions = useMemo(
    () => runForceLayout(nodes, links, width, height),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [nodes.map((n) => n.id).join(","), links.length, width, height],
  );

  const connectedIds = useMemo(() => {
    if (!hoveredId) return null;
    const ids = new Set<string>([hoveredId]);
    for (const l of links) {
      if (l.source === hoveredId) ids.add(l.target);
      if (l.target === hoveredId) ids.add(l.source);
    }
    return ids;
  }, [hoveredId, links]);

  if (!nodes.length) return null;

  const gradientId = (n: GraphNode) => `node-grad-${(n.type ?? "detail")}`;
  const linkGradientId = (link: GraphLink) =>
    `link-grad-${nodes.findIndex((n) => n.id === link.source)}-${nodes.findIndex((n) => n.id === link.target)}`;

  // Resolve fill: if `type` is set use the gradient, otherwise fall back to
  // the flat `color` (legacy callers like analytics/mind-maps pass cluster
  // colours directly).
  const fillFor = (n: GraphNode): string => {
    if (n.type) return `url(#${gradientId(n)})`;
    return n.color ?? PALETTE.detail.solid;
  };
  // Solid (non-gradient) colour, used for halos / labels.
  const solidFor = (n: GraphNode): string => {
    if (n.type) return paletteFor(n).solid;
    return n.color ?? PALETTE.detail.solid;
  };

  return (
    <svg
      width={width}
      height={height}
      style={{ display: "block", background: "transparent" }}
      viewBox={`0 0 ${width} ${height}`}
    >
      <defs>
        {/* Background grid pattern */}
        <pattern id="grid-pattern" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(148,163,184,0.08)" strokeWidth="1" />
        </pattern>

        {/* Background radial glow */}
        <radialGradient id="bg-radial" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stopColor="rgba(124,58,237,0.10)" />
          <stop offset="100%" stopColor="rgba(124,58,237,0)" />
        </radialGradient>

        {/* Per-type node gradients */}
        {Object.entries(PALETTE).map(([key, p]) => (
          <radialGradient key={key} id={`node-grad-${key}`} cx="35%" cy="30%" r="80%">
            <stop offset="0%" stopColor={p.from} stopOpacity="1" />
            <stop offset="100%" stopColor={p.to} stopOpacity="1" />
          </radialGradient>
        ))}

        {/* Per-link gradients (source → target colour) */}
        {links.map((link, i) => {
          const sNode = nodes.find((n) => n.id === link.source);
          const tNode = nodes.find((n) => n.id === link.target);
          if (!sNode || !tNode) return null;
          const s = positions.get(link.source);
          const t = positions.get(link.target);
          if (!s || !t) return null;
          const sCol = solidFor(sNode);
          const tCol = solidFor(tNode);
          return (
            <linearGradient
              key={i}
              id={linkGradientId(link)}
              gradientUnits="userSpaceOnUse"
              x1={s.x} y1={s.y} x2={t.x} y2={t.y}
            >
              <stop offset="0%" stopColor={sCol} stopOpacity="0.7" />
              <stop offset="100%" stopColor={tCol} stopOpacity="0.7" />
            </linearGradient>
          );
        })}

        {/* Soft outer glow for hovered nodes */}
        <filter id="node-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        <filter id="node-shadow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="3" stdDeviation="4" floodOpacity="0.25" />
        </filter>

        <filter id="text-bg" x="-5%" y="-20%" width="110%" height="140%">
          <feFlood floodColor="white" floodOpacity="0.92" />
          <feComposite in="SourceGraphic" operator="over" />
        </filter>
      </defs>

      {/* Background layers */}
      <rect width={width} height={height} fill="url(#grid-pattern)" />
      <rect width={width} height={height} fill="url(#bg-radial)" />

      {/* ── Links ─────────────────────────────────────────────────────── */}
      {links.map((link, i) => {
        const s = positions.get(link.source);
        const t = positions.get(link.target);
        if (!s || !t) return null;
        const isHighlighted =
          !hoveredId || (connectedIds?.has(link.source) && connectedIds?.has(link.target));
        const isFocused = hoveredId !== null && isHighlighted;
        const strokeW = Math.max(1.2, link.weight * 4) * (isFocused ? 1.6 : 1);

        // Curved bezier
        const mx = (s.x + t.x) / 2 + (t.y - s.y) * 0.12;
        const my = (s.y + t.y) / 2 - (t.x - s.x) * 0.12;

        return (
          <g key={i}>
            <path
              d={`M ${s.x} ${s.y} Q ${mx} ${my} ${t.x} ${t.y}`}
              fill="none"
              stroke={`url(#${linkGradientId(link)})`}
              strokeWidth={strokeW}
              strokeLinecap="round"
              opacity={isHighlighted ? (isFocused ? 1 : 0.65) : 0.08}
              style={{ transition: "opacity 0.2s, stroke-width 0.2s" }}
            />
          </g>
        );
      })}

      {/* ── Nodes ─────────────────────────────────────────────────────── */}
      {nodes.map((node) => {
        const pos = positions.get(node.id);
        if (!pos) return null;
        const radius = 10 + node.val * 0.55;
        const isHovered = node.id === hoveredId;
        const isConnected = connectedIds?.has(node.id) ?? false;
        const dimmed = hoveredId !== null && !isHovered && !isConnected;
        const solid = solidFor(node);
        const fill = fillFor(node);
        const isCentral = node.type === "central";

        // Label sizing — central + primary nodes show label INSIDE; small nodes get external label
        const showInternalLabel = radius >= 22;
        const fontSize = isCentral ? 13 : showInternalLabel ? 11 : 10;
        const maxChars = showInternalLabel ? Math.floor(radius * 1.6) : 28;
        const truncated = node.label.length > maxChars;
        const innerLabel = truncated ? node.label.slice(0, maxChars - 1) + "…" : node.label;

        return (
          <g
            key={node.id}
            onMouseEnter={() => setHoveredId(node.id)}
            onMouseLeave={() => setHoveredId(null)}
            style={{ cursor: "pointer", transition: "opacity 0.2s" }}
            opacity={dimmed ? 0.18 : 1}
          >
            {/* Pulse ring on central node + on hover */}
            {(isCentral || isHovered) && (
              <>
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={radius + 14}
                  fill="none"
                  stroke={solid}
                  strokeWidth={2}
                  opacity={0.25}
                >
                  {isCentral && (
                    <animate
                      attributeName="r"
                      from={radius + 6}
                      to={radius + 22}
                      dur="2.4s"
                      repeatCount="indefinite"
                    />
                  )}
                  {isCentral && (
                    <animate
                      attributeName="opacity"
                      from="0.5"
                      to="0"
                      dur="2.4s"
                      repeatCount="indefinite"
                    />
                  )}
                </circle>
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={radius + 6}
                  fill="none"
                  stroke={solid}
                  strokeWidth={2.5}
                  opacity={isHovered ? 0.65 : 0.35}
                />
              </>
            )}

            {/* Main node */}
            <circle
              cx={pos.x}
              cy={pos.y}
              r={radius}
              fill={fill}
              stroke="white"
              strokeWidth={isHovered ? 3 : 2}
              filter={isHovered ? "url(#node-glow)" : "url(#node-shadow)"}
              style={{ transition: "stroke-width 0.15s, filter 0.15s" }}
            />

            {/* Specular highlight (subtle) */}
            <ellipse
              cx={pos.x - radius * 0.35}
              cy={pos.y - radius * 0.45}
              rx={radius * 0.45}
              ry={radius * 0.25}
              fill="rgba(255,255,255,0.35)"
              style={{ pointerEvents: "none" }}
            />

            {/* Internal label (large nodes only) */}
            {showInternalLabel && (
              <text
                x={pos.x}
                y={pos.y + fontSize * 0.36}
                textAnchor="middle"
                fontSize={fontSize}
                fontWeight="700"
                fontFamily="system-ui, -apple-system, sans-serif"
                fill="white"
                style={{
                  pointerEvents: "none",
                  userSelect: "none",
                  textShadow: "0 1px 2px rgba(0,0,0,0.3)",
                }}
              >
                {innerLabel}
              </text>
            )}

            {/* External label (small nodes + always on hover) */}
            {(!showInternalLabel || isHovered) && (
              <g style={{ pointerEvents: "none" }}>
                <rect
                  x={pos.x - Math.max(node.label.length, 4) * 3.4}
                  y={pos.y + radius + 4}
                  width={Math.max(node.label.length, 4) * 6.8}
                  height={18}
                  rx={9}
                  ry={9}
                  fill="white"
                  stroke={solid}
                  strokeWidth={1.2}
                  opacity={0.95}
                />
                <text
                  x={pos.x}
                  y={pos.y + radius + 16}
                  textAnchor="middle"
                  fontSize={10.5}
                  fontWeight="600"
                  fontFamily="system-ui, -apple-system, sans-serif"
                  fill={solid}
                  style={{ userSelect: "none" }}
                >
                  {node.label.length > 22 ? node.label.slice(0, 21) + "…" : node.label}
                </text>
              </g>
            )}
          </g>
        );
      })}
    </svg>
  );
}
