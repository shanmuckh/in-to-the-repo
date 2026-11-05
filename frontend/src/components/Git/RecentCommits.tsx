'use client';

import React from 'react';

type Commit = {
  message: string;
  author: string;
  date: string;
  sha: string;
};

type RecentCommitsProps = {
  recent_commits: Commit[];
};

export const RecentCommits: React.FC<RecentCommitsProps> = ({ recent_commits }) => {
  if (!recent_commits || recent_commits.length === 0) {
    return (
      <div className="text-neutral-400 text-sm italic">
        No recent commits available.
      </div>
    );
  }

  return (
    <div className="bg-neutral-900 py-6 rounded-xl shadow-lg w-full h-full border border-neutral-700 text-white overflow-hidden">
      <h2 className="text-2xl px-6 font-semibold mb-4 text-purple-400">Recent Commits</h2>
      <ul className="custom-scrollbar space-y-2 px-6 overflow-auto h-full pb-10">
        {recent_commits.map((commit, idx) => (
          <li key={idx} className="bg-neutral-800 p-4 rounded-md border border-neutral-700">
            <p className="font-medium text-neutral-200 break-all">{commit.message}</p>
            <div className="text-sm text-neutral-400 mt-1">
              <span>By <span className="text-neutral-300">{commit.author}</span></span> •{' '}
              <span>{new Date(commit.date).toLocaleString()}</span>
            </div>
            <div className="text-xs text-neutral-500 mt-1 break-all">Commit: {commit.sha}</div>
          </li>
        ))}
      </ul>
    </div>
  );
};
