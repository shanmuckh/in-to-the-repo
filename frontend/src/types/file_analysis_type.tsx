// types/analysis.ts

export type TutorialStep = {
  lines: number | [number, number];
  step: string;
};

export type NodeData = {
  data: {
    label: string;
  };
  id: string;
  position: {
    x: number;
    y: number;
  };
};

export type EdgeData = {
  animated: boolean;
  id: string;
  source: string;
  target: string;
  type?: string;
};

export type Graph = {
  edges: EdgeData[];
  nodes: NodeData[];
};

export type FileAnalysis = {
  analysis: {
    code: string;
    error?:string;
    language: string;
    summary?: string;
    tutorial?: TutorialStep[];
    auth_required?: boolean;
  };
  call_graph: Graph;
  file_graph: Graph;
  file_path: string;
};
