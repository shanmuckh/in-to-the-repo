import { GitAnalysis } from "@/types/git_analysis_type";
import { Graph } from "@/types/file_analysis_type";

export type ImportMetadata = {
  type: 'default' | 'named' | 'namespace' | null;
  is_third_party: boolean;
};

export type ImportInfo = {
  content: string;
  start_line: number;
  source_module: string | null;
  imported_items: string[];
  metadata: ImportMetadata;
};

export type ClassMetadata = {
  type: string;
  complexity: number;
};

export type ClassInfo = {
  name: string;
  content: string;
  start_line: number;
  methods: string[];
  metadata: ClassMetadata;
};

export type FunctionMetadata = {
  type: string;
  complexity: number;
};

export type FunctionInfo = {
  name: string;
  content: string;
  start_line: number;
  metadata: FunctionMetadata;
};

export type CallLocation = {
  line: number;
  column: number;
};

export type FunctionCall = {
  caller: string | null;
  callee: string;
  location: CallLocation;
};

export type RecentCommit = {
    author: string,
    date: string,
    message: string,
    sha: string
}

export type GitInfo = {
  commit_count: number;
  last_modified: string | null;
  recent_commits: RecentCommit[];
};

export type ASTFileData = {
  language: string;
  imports: ImportInfo[];
  classes: ClassInfo[];
  functions: FunctionInfo[];
  calls: FunctionCall[];
  git_info: GitInfo;
};

export type ASTResult = {
  [filePath: string]: ASTFileData;
};

export type RepoAnalysis = {
    ast: ASTResult,
    dependency_graph: Graph,
}

export type Analysis = {
    branch: string,
    git_analysis: GitAnalysis,
    repo_analysis:RepoAnalysis,
    repo_url:string
}
