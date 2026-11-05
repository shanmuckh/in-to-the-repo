import React from 'react';

interface Contributor {
  name: string;
  commits: number;
  avatar_url?: string;
}

interface TopContributorsProps {
  contributors: Contributor[];
  total_commits: number;
}

export const TopContributors: React.FC<TopContributorsProps> = ({ contributors,total_commits }) => {
  return (
    <div className="bg-neutral-900 py-6 rounded-xl shadow-lg w-full h-full  border border-neutral-700 text-white overflow-hidden">
        <div className='text-2xl px-6 font-semibold mb-4 text-wrap text-purple-400 '>Top Contributors {(total_commits > 50) ? '(Based on Latest 50 Commits)' : ''}</div>
        
      <ul className="custom-scrollbar px-6 space-y-2 max-h-56 overflow-auto h-full">
        {contributors.map((contributor, index) => (
          <li key={index} className="flex justify-between gap-2">
            <span className="break-all ">{contributor.name}</span>
            <span className="text-neutral-400 text-nowrap">{contributor.commits} changes</span>
          </li>
        ))}
      </ul>
    </div>
  );
};
