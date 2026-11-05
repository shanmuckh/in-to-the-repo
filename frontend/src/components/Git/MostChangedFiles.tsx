import React from 'react';

interface FileChange {
  file: string;
  changes: number;
}

interface MostChangedFilesProps {
  files: FileChange[];
  total_commits:number;
}

export const MostChangedFiles: React.FC<MostChangedFilesProps> = ({ files,total_commits }) => {
  return (
    <div className="bg-neutral-900 rounded-xl py-6 shadow-lg w-full h-full   border border-neutral-700 text-white overflow-hidden">
        <div className='text-2xl px-6 font-semibold mb-4 text-wrap text-purple-400 '>Top Modified Files {(total_commits > 50) ? '(Based on Latest 50 Commits)' : ''}</div>
      <ul className="custom-scrollbar px-6 space-y-2 max-h-56 overflow-auto h-full">
        {files.map((file, index) => (
          <li key={index} className="flex justify-between gap-2">
            <span className="break-all ">{file.file}</span>
            <span className="text-neutral-400 text-nowrap">{file.changes} changes</span>
          </li>
        ))}
      </ul>
    </div>
  );
};
