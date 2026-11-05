'use client';

import React, { useEffect, useState } from 'react';
import { ReactFlow, Controls } from '@xyflow/react';
import type { Node as FlowNode } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { getLayoutedGraph } from '@/components/Graph/Layout';
import Loading from '../Loading';
import { motion, AnimatePresence } from 'framer-motion';
import { Analysis, ASTFileData, ASTResult } from '@/types/repo_analysis_type';
import axios from 'axios';
import { getAnalysisByIdRoute } from '@/utils/APIRoutes';

function ArchitectureGraph() {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("Retrieving architecture map...");
  const [selectedNode, setSelectedNode] = useState<FlowNode | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);
  const [fileInfo, setFileInfo] = useState<ASTFileData | null>(null);

  useEffect(() => {
    const handleClickOutside = () => {
      setSelectedNode(null);
      setTooltipPos(null);
      setFileInfo(null);
    };
    window.addEventListener('click', handleClickOutside);
    return () => {
      window.removeEventListener('click', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    setLoading(true);
    async function fetchAnalysis() {
      // Get repo_analysis_id from session
      const repoAnalysisId = sessionStorage.getItem('currentRepoAnalysisId');
      if (!repoAnalysisId) {
        setMessage("No analysis ID found. Please search for a repository.");
        setLoading(false);
        return;
      }

      try {
        // Fetch analysis from API
        const response = await axios.get(getAnalysisByIdRoute(parseInt(repoAnalysisId)));
        const analysisData: Analysis = {
          repo_url: response.data.repo_url,
          branch: response.data.branch,
          repo_analysis: response.data.repo_analysis,
          git_analysis: response.data.git_analysis
        };
        setAnalysis(analysisData);
      } catch (err) {
        console.error("[ARCHITECTURE] Error fetching analysis:", err);
        setMessage("Failed to load architecture map.");
      } finally {
        setLoading(false);
      }
    }
    fetchAnalysis();
  }, []);

  const { nodes, edges } = analysis
    ? getLayoutedGraph(
        analysis.repo_analysis.dependency_graph.nodes,
        analysis.repo_analysis.dependency_graph.edges,
        'TB'
      )
    : { nodes: [], edges: [] };

  const proOptions = { hideAttribution: true };

  const findMatchingFile = (nodeId: string, ast: ASTResult): ASTFileData | null => {
    const matchEntry = Object.entries(ast).find(([filePath]) => {
      const nameWithoutExt = filePath.replace(/\.[^/.]+$/, '');
      return nameWithoutExt === nodeId;
    });
    return matchEntry ? matchEntry[1] : null;
  };

  const handleNodeClick = async (event: React.MouseEvent, node: FlowNode) => {
    event.preventDefault();
    event.stopPropagation();
    setSelectedNode(node);
    setTooltipPos({ x: event.clientX, y: event.clientY  + 10 });

    if (analysis) {
      const match = findMatchingFile(node.id, analysis.repo_analysis.ast);
      setFileInfo(match);
    }
  };

  return (
    <div className='h-full w-full'>
      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className='-mt-24'
          >
            <Loading message={message} />
          </motion.div>
        ) : (
          <motion.div
            key="graph"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            style={{ height: '100%', width: '100%' }}
          >
            <ReactFlow
              defaultNodes={nodes}
              defaultEdges={edges}
              fitView
              proOptions={proOptions}
              onNodeClick={handleNodeClick}
              nodesDraggable
              nodesConnectable={false} 
            >
              <Controls />
            </ReactFlow>

            {selectedNode && tooltipPos && (
              <motion.div
                onClick={(e) => e.stopPropagation()}
                className="fixed z-50 bg-white shadow-xl rounded-md p-3 border border-gray-200 text-sm text-gray-800 -translate-x-1/2"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                style={{
                  top: tooltipPos.y,
                  left: tooltipPos.x,
                  minWidth: 220,
                }}
              >
                <p className="font-semibold">{selectedNode.id}</p>
                <p className="text-xs text-gray-500 mb-1">
                  {String(selectedNode.data?.label || 'No label')}
                </p>

                {fileInfo && (
                  <>
                    <p><strong>Language:</strong> {fileInfo.language}</p>
                    <p><strong>Last modified:</strong> {fileInfo.git_info?.last_modified || 'N/A'}</p>
                    <p><strong>Functions:</strong> {fileInfo.functions?.length || 0}</p>
                    <p><strong>Classes:</strong> {fileInfo.classes?.length || 0}</p>
                    <p><strong>Imports:</strong> {fileInfo.imports?.length || 0}</p>
                  </>
                )}
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default ArchitectureGraph;
