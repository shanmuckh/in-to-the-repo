import dagre from 'dagre';
import { Node, Edge, Position } from '@xyflow/react';

const nodeWidth = 180;
const nodeHeight = 60;
const colGap = 40;
const rowGap = 50;
const rankGap = 110;

/** Shared React Flow props: let fitView zoom out far enough for big repos. */
export const graphViewProps = {
  fitView: true,
  fitViewOptions: { padding: 0.12 },
  minZoom: 0.05,
  maxZoom: 2,
} as const;

/**
 * Lay out a graph top-to-bottom with dagre, then make it readable:
 *  - ranks wider than `maxPerRow` wrap onto several rows (a file with 60
 *    functions becomes a compact grid instead of one 10,000px-wide line)
 *  - nodes with no edges are gathered into a grid below the connected part
 * A fresh dagre graph is built per call so earlier graphs don't leak in.
 */
export function getLayoutedGraph(
  nodes: Node[],
  edges: Edge[],
  direction: 'TB' | 'LR' = 'TB',
  maxPerRow = 8
): { nodes: Node[]; edges: Edge[] } {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: direction, nodesep: colGap, ranksep: rankGap });

  const connected = new Set<string>();
  edges.forEach((e) => {
    connected.add(e.source);
    connected.add(e.target);
  });
  const linked = nodes.filter((n) => connected.has(n.id));
  const isolated = nodes.filter((n) => !connected.has(n.id));

  linked.forEach((n) => g.setNode(n.id, { width: nodeWidth, height: nodeHeight }));
  edges.forEach((e) => {
    if (g.hasNode(e.source) && g.hasNode(e.target)) g.setEdge(e.source, e.target);
  });
  dagre.layout(g);

  const targetPosition: Position = direction === 'LR' ? Position.Left : Position.Top;
  const sourcePosition: Position = direction === 'LR' ? Position.Right : Position.Bottom;
  const positions = new Map<string, { x: number; y: number }>();

  // Group linked nodes by dagre rank (same y in TB, same x in LR), keep dagre's order.
  const rankKey = (id: string) => Math.round(direction === 'LR' ? g.node(id).x : g.node(id).y);
  const along = (id: string) => (direction === 'LR' ? g.node(id).y : g.node(id).x);
  const ranks = new Map<number, string[]>();
  linked.forEach((n) => {
    const k = rankKey(n.id);
    ranks.set(k, [...(ranks.get(k) ?? []), n.id]);
  });

  const placeGrid = (ids: string[], start: number) => {
    const perRow = Math.min(maxPerRow, ids.length);
    ids.forEach((id, i) => {
      const row = Math.floor(i / perRow);
      const inRow = Math.min(perRow, ids.length - row * perRow);
      const col = i % perRow;
      const offset = (col - (inRow - 1) / 2) * (nodeWidth + colGap);
      const depth = start + row * (nodeHeight + rowGap);
      positions.set(id, direction === 'LR' ? { x: depth, y: offset } : { x: offset, y: depth });
    });
    return start + Math.ceil(ids.length / perRow) * (nodeHeight + rowGap);
  };

  let cursor = 0;
  [...ranks.keys()]
    .sort((a, b) => a - b)
    .forEach((k) => {
      const ids = ranks.get(k)!.sort((a, b) => along(a) - along(b));
      cursor = placeGrid(ids, cursor) + (rankGap - rowGap);
    });
  if (isolated.length) {
    placeGrid(isolated.map((n) => n.id), cursor + (linked.length ? rankGap : 0));
  }

  const layoutedNodes = nodes.map((node) => {
    const p = positions.get(node.id) ?? { x: 0, y: 0 };
    return {
      ...node,
      position: { x: p.x - nodeWidth / 2, y: p.y - nodeHeight / 2 },
      targetPosition,
      sourcePosition,
    };
  });

  return { nodes: layoutedNodes, edges };
}
