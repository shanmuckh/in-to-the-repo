'use client';

import React from 'react';

type ProjectSummaryProps = {
  repo: string;
  total_commits: number;
  first_commit_date: string;
  last_commit_date: string;
  owner: string;
  branch?: string;
  description?: string | null;
};

export const ProjectSummary: React.FC<ProjectSummaryProps> = ({
  repo,
  total_commits,
  first_commit_date,
  last_commit_date,
  owner,
  branch,
  description,
}) => {
  return (
    <div className="bg-neutral-900 py-6 rounded-xl shadow-lg w-full h-full  border border-neutral-700 text-white overflow-hidden">
      <h2 className="text-2xl px-6 font-semibold mb-4 text-purple-400">Project Summary</h2>

      <div className="custom-scrollbar space-y-2 px-6 text-sm sm:text-base h-full max-h-56 overflow-auto">
        <div><span className="font-medium text-neutral-300">Repository:</span> {repo}</div>
        <div><span className="font-medium text-neutral-300">Owner:</span> {owner}</div>
        {branch && (
          <div><span className="font-medium text-neutral-300">Default Branch:</span> {branch}</div>
        )}
        <div><span className="font-medium text-neutral-300">Total Commits:</span> {total_commits}</div>
        <div><span className="font-medium text-neutral-300">First Commit:</span> {new Date(first_commit_date).toLocaleDateString()}</div>
        <div><span className="font-medium text-neutral-300">Last Commit:</span> {new Date(last_commit_date).toLocaleDateString()}</div>
        {description && (
          <div>
            <span className="font-medium text-neutral-300">Description:</span>
            <p className="mt-1 text-neutral-400">{description}</p>
          </div>
        )}
      </div>
    </div>
  );
};
