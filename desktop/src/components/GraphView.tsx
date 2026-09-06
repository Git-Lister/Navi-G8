// desktop/src/components/GraphView.tsx

import React, { useRef, useEffect } from 'react';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';

interface GraphNode {
  id: string;
  label: string;
  type: 'trajectory' | 'stream' | 'perturbation' | 'clarification' | 'flag' | 'session';
  volatility?: number;
  status?: string;
  description?: string;
}

interface GraphEdge {
  id: string;
  from: string;
  to: string;
  label?: string;
}

interface GraphViewProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (nodeId: string) => void;
}

const GraphView: React.FC<GraphViewProps> = ({ nodes, edges, onNodeClick }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);

  const getColor = (type: string): string => {
    switch (type) {
      case 'trajectory': return '#f5b342';
      case 'stream': return '#4ad8e0';
      case 'perturbation': return '#eb5757';
      case 'clarification': return '#6fcf97';
      case 'flag': return '#9b9b9b';
      case 'session': return '#8e44ad';
      default: return '#ffffff';
    }
  };

  const getSize = (node: GraphNode): number => {
    if (node.type === 'trajectory') return 30;
    if (node.type === 'stream') return 20 + (node.volatility || 0) * 30;
    if (node.type === 'perturbation') return 25;
    if (node.type === 'clarification') return 22;
    if (node.type === 'flag') return 18;
    return 20;
  };

  useEffect(() => {
    if (!containerRef.current) return;

    const nodeDataSet = new DataSet(
      nodes.map(node => ({
        id: node.id,
        label: node.label || node.id.slice(0, 8),
        color: { background: getColor(node.type), border: '#2a2a30' },
        size: getSize(node),
        shape: node.type === 'perturbation' ? 'diamond' : 'dot',
        title: node.description || node.type,
        font: { color: '#e8e8ed', size: 12 },
      }))
    );

    const edgeDataSet = new DataSet(
      edges.map(edge => ({
        id: edge.id,
        from: edge.from,
        to: edge.to,
        label: edge.label || '',
        color: { color: '#4a4a55' },
        arrows: 'to',
        font: { color: '#8a8a9a', size: 10, align: 'middle' },
      }))
    );

    const options = {
      physics: {
        enabled: true,
        stabilization: { iterations: 100 },
        solver: 'forceAtlas2Based' as const,
      },
      interaction: { hover: true, tooltipDelay: 200 },
      layout: { improvedLayout: true },
      nodes: { borderWidth: 2, shadow: true },
      edges: {
        smooth: { enabled: true, type: 'continuous' as const, roundness: 0.5 },
      },
      height: '100%',
      width: '100%',
    };

    const network = new Network(
      containerRef.current,
      { nodes: nodeDataSet, edges: edgeDataSet },
      options
    );
    networkRef.current = network;

    network.on('click', (params: { nodes: string[] }) => {
      if (params.nodes.length > 0 && onNodeClick) {
        onNodeClick(params.nodes[0]);
      }
    });

    return () => network.destroy();
  }, []);

  useEffect(() => {
    if (!networkRef.current) return;
    const network = networkRef.current;

    const nodeDataSet = new DataSet(
      nodes.map(node => ({
        id: node.id,
        label: node.label || node.id.slice(0, 8),
        color: { background: getColor(node.type), border: '#2a2a30' },
        size: getSize(node),
        shape: node.type === 'perturbation' ? 'diamond' : 'dot',
        title: node.description || node.type,
        font: { color: '#e8e8ed', size: 12 },
      }))
    );

    network.setData({
      nodes: nodeDataSet,
      edges: new DataSet(
        edges.map(edge => ({
          id: edge.id,
          from: edge.from,
          to: edge.to,
          label: edge.label || '',
          color: { color: '#4a4a55' },
          arrows: 'to',
          font: { color: '#8a8a9a', size: 10, align: 'middle' },
        }))
      ),
    });
  }, [nodes, edges]);

  return (
    <div
      ref={containerRef}
      className="graph-view-container"
      style={{ width: '100%', height: '100%', backgroundColor: '#0d0d0f' }}
    />
  );
};

export default GraphView;