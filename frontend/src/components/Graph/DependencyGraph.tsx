import React, { useState,useEffect } from "react";
import { ReactFlow, Controls } from "@xyflow/react";
import type { Node as FlowNode } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { getLayoutedGraph } from "@/components/Graph/Layout";
import { FileAnalysis } from "@/types/file_analysis_type";
import {
  ASTFileData,
  ClassInfo,
  FunctionInfo,
} from "@/types/repo_analysis_type";
import { AnimatePresence } from "motion/react";
import { motion } from "framer-motion";

function DependencyGraph({
  analysis,
  fileAST,
}: {
  analysis: FileAnalysis;
  fileAST: ASTFileData;
}) {
  const [selectedNode, setSelectedNode] = useState<FlowNode | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);
  const [nodeInfo, setNodeInfo] = useState<
    | ASTFileData
    | FunctionInfo
    | ClassInfo
    | { method: string; class: ClassInfo }
    | null
  >(null);

    useEffect(() => {
      const handleClickOutside = () => {
        setSelectedNode(null);
        setTooltipPos(null);
        setNodeInfo(null);
      };
      window.addEventListener('click', handleClickOutside);
      return () => {
        window.removeEventListener('click', handleClickOutside);
      };
    }, []);

  if (!analysis) return <div>Loading graph...</div>;
  console.log(analysis);

  const { nodes, edges } = getLayoutedGraph(
    analysis.file_graph.nodes,
    analysis.file_graph.edges,
    "TB"
  );

  const findMatchingDetail = (
    nodeId: string,
    ast: ASTFileData
  ):
    | ASTFileData
    | FunctionInfo
    | ClassInfo
    | { method: string; class: ClassInfo }
    | null => {
    let isFile = false;
    let isFunction = false;
    let isClass = false;
    let isClassMethod = false;

    let functionName = "";
    let className = "";
    let methodName = "";

    if (nodeId.includes("::function::")) {
      isFunction = true;
      [, functionName] = nodeId.split("::function::");
    } else if (nodeId.includes("::class::")) {
      const [, classPart] = nodeId.split("::class::");

      if (classPart.includes("::method::")) {
        isClassMethod = true;
        [className, methodName] = classPart.split("::method::");
      } else {
        isClass = true;
        className = classPart;
      }
    } else {
      isFile = true;
    }

    if (isFunction) {
      return ast.functions.find((fn) => fn.name === functionName) || null;
    }

    if (isClass) {
      return ast.classes.find((cls) => cls.name === className) || null;
    }

    if (isClassMethod) {
      const cls = ast.classes.find((cls) => cls.name === className);
      if (cls && cls.methods.includes(methodName)) {
        return { method: methodName, class: cls };
      }
    }
    if (isFile) {
      return ast;
    }

    return null; // Fallback for unmatched cases
  };

  const handleNodeClick = async (event: React.MouseEvent, node: FlowNode) => {
    event.preventDefault();
    event.stopPropagation();
    setSelectedNode(node);
    setTooltipPos({ x: event.clientX, y: event.clientY + 10  });

    if (analysis) {
      const match = findMatchingDetail(node.id, fileAST);
      setNodeInfo(match);
    }
  };
  const proOptions = { hideAttribution: true };

  return (
    <div className="h-full w-full">
      <AnimatePresence>
        <motion.div
          key="graph"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5 }}
          style={{ height: "100%", width: "100%" }}
        >
          <ReactFlow
            defaultNodes={nodes}
            defaultEdges={edges}
            fitView
            proOptions={proOptions}
            nodesDraggable
            onNodeClick={handleNodeClick}
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
              <p className="text-xs text-gray-500 mb-1">
                {String(selectedNode.data?.label || "No label")}
              </p>

              {nodeInfo && (
                <>
                  {"language" in nodeInfo && (
                    <>
                      <p>
                        <strong>Type: </strong>File
                      </p>
                      <p>
                        <strong>Language: </strong> {nodeInfo.language}
                      </p>
                      <p>
                        <strong>Last modified:</strong>{" "}
                        {nodeInfo.git_info?.last_modified || "N/A"}
                      </p>
                    </>
                  )}
                  {"method" in nodeInfo && "class" in nodeInfo && (
                    <>
                      <p>
                        <strong>Type: </strong>Class Method
                      </p>
                      <p>
                        <strong>Class: </strong> {nodeInfo.class.name}
                      </p>
                      <p>
                        <strong>Method: </strong> {nodeInfo.method}
                      </p>
                    </>
                  )}
                  {"methods" in nodeInfo && (
                    <>
                      <p>
                        <strong>Type: </strong>Class
                      </p>
                      <p>
                        <strong>Class: </strong>
                        {nodeInfo.name}
                      </p>
                      <p>
                        <strong>Total Methods: </strong>
                        {nodeInfo.methods.length}
                      </p>
                      <p>
                        <strong>Complexity: </strong>
                        {nodeInfo.metadata.complexity}
                      </p>
                      <p>
                        <strong>Line: </strong>
                        {nodeInfo.start_line}
                      </p>
                    </>
                  )}
                  {"name" in nodeInfo && !("methods" in nodeInfo) && (
                    <>
                      <p>
                        <strong>Type: </strong>Function
                      </p>
                      <p>
                        <strong>Function: </strong>
                        {nodeInfo.name}
                      </p>
                      <p>
                        <strong>Complexity: </strong>
                        {nodeInfo.metadata.complexity}
                      </p>
                      <p>
                        <strong>Line: </strong>
                        {nodeInfo.start_line}
                      </p>
                    </>
                  )}
                </>
              )}
            </motion.div>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

export default DependencyGraph;
