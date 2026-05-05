"use client";

import { useMemo, useState } from "react";

export interface GraphNode {
  id: string;
  label: string;
  color: string;
  val: number; // controls radius: radius = 6 + val * 0.5
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

function runForceLayout(
  nodes: GraphNode[],
  links: GraphLink[],
  width: number,
  height: number
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
  const REPULSION = 2200;
  const DECAY = 0.86;

  for (let t = 0; t < ITERATIONS; t++) {
    const alpha = 0.4 * Math.pow(0.985, t);

    // Repulsion between all node pairs
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

    // Spring attraction for links
    for (const link of links) {
      const s = positions.get(link.source);
      const t2 = positions.get(link.target);
      if (!s || !t2) continue;
      const dx = t2.x - s.x;
      const dy = t2.y - s.y;
      const d = Math.sqrt(dx * dx + dy * dy) + 0.1;
      const sNode = nodes.find((n) => n.id === link.source);
      const tNode = nodes.find((n) => n.id === link.target);
      const restLen = 70 + (sNode?.val ?? 6) + (tNode?.val ?? 6);
      const force = (d - restLen) * 0.06 * alpha;
      const fx = (dx / d) * force;
      const fy = (dy / d) * force;
      s.vx += fx;
      s.vy += fy;
      t2.vx -= fx;
      t2.vy -= fy;
    }

    // Gravity toward center
    for (const [, p] of positions) {
      p.vx += (cx - p.x) * 0.025 * alpha;
      p.vy += (cy - p.y) * 0.025 * alpha;
      p.vx *= DECAY;
      p.vy *= DECAY;
      p.x += p.vx;
      p.y += p.vy;
    }
  }

  // Normalize to fit in viewport with padding
  const PAD = 60;
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
    [nodes.map((n) => n.id).join(","), links.length, width, height]
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

  return (
    <svg
      width={width}
      height={height}
      style={{ display: "block" }}
      viewBox={`0 0 ${width} ${height}`}
    >
      <defs>
        <filter id="node-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.15" />
        </filter>
      </defs>

      {/* Links */}
      {links.map((link, i) => {
        const s = positions.get(link.source);
        const t = positions.get(link.target);
        if (!s || !t) return null;
        const isHighlighted =
          !hoveredId ||
          (connectedIds?.has(link.source) && connectedIds?.has(link.target));
        const strokeW = Math.max(0.8, link.weight * 3.5);
        // Curved bezier
        const mx = (s.x + t.x) / 2 + (t.y - s.y) * 0.1;
        const my = (s.y + t.y) / 2 - (t.x - s.x) * 0.1;
        return (
          <path
            key={i}
            d={`M ${s.x} ${s.y} Q ${mx} ${my} ${t.x} ${t.y}`}
            fill="none"
            stroke="rgba(100,116,139,0.35)"
            strokeWidth={strokeW}
            opacity={isHighlighted ? 1 : 0.08}
            style={{ transition: "opacity 0.2s" }}
          />
        );
      })}

      {/* Nodes */}
      {nodes.map((node) => {
        const pos = positions.get(node.id);
        if (!pos) return null;
        const radius = 6 + node.val * 0.55;
        const isHovered = node.id === hoveredId;
        const isConnected = connectedIds?.has(node.id) ?? false;
        const dimmed = hoveredId !== null && !isHovered && !isConnected;
        const fontSize = radius > 18 ? 12 : radius > 12 ? 10 : 9;
        // Truncate label to fit in circle
        const maxChars = Math.floor(radius * 1.6);
        const label =
          node.label.length > maxChars
            ? node.label.slice(0, maxChars - 1) + "…"
            : node.label;

        return (
          <g
            key={node.id}
            onMouseEnter={() => setHoveredId(node.id)}
            onMouseLeave={() => setHoveredId(null)}
            style={{ cursor: "pointer", transition: "opacity 0.2s" }}
            opacity={dimmed ? 0.15 : 1}
          >
            {/* Glow ring on hover */}
            {isHovered && (
              <circle
                cx={pos.x}
                cy={pos.y}
                r={radius + 6}
                fill="none"
                stroke={node.color}
                strokeWidth={2}
                opacity={0.4}
              />
            )}
            <circle
              cx={pos.x}
              cy={pos.y}
              r={radius}
              fill={node.color}
              stroke="white"
              strokeWidth={isHovered ? 2.5 : 1.5}
              filter="url(#node-shadow)"
              style={{ transition: "r 0.15s" }}
            />
            <text
              x={pos.x}
              y={pos.y + fontSize * 0.35}
              textAnchor="middle"
              fontSize={fontSize}
              fontWeight="600"
              fontFamily="system-ui, sans-serif"
              fill="white"
              style={{ pointerEvents: "none", userSelect: "none" }}
            >
              {label}
            </text>
            {/* Tooltip-style label below for large nodes or hover */}
            {(isHovered || radius > 22) && node.label.length > maxChars && (
              <text
                x={pos.x}
                y={pos.y + radius + 14}
                textAnchor="middle"
                fontSize={10}
                fill="#475569"
                fontFamily="system-ui, sans-serif"
                style={{ pointerEvents: "none", userSelect: "none" }}
              >
                {node.label}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
