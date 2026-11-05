type Contributor = {
  name: string;
  commits: number;
};

type ChangedFile = {
  file: string;
  changes: number;
};

type Commit = {
  sha: string;
  message: string;
  author: string;
  date: string; // ISO 8601 format
};

export type GitAnalysis = {
  repo: string;
  owner: string;
  default_branch: string;
  description: string | null;
  total_commits_fetched: number;
  top_contributors: Contributor[];
  most_changed_files: ChangedFile[];
  commit_activity_by_day: Record<string, number>; // date as 'YYYY-MM-DD' => number of commits
  recent_commits: Commit[];
  first_commit_date: string; // ISO 8601 format
  last_commit_date: string;  // ISO 8601 format
};
