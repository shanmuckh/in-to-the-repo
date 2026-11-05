'use client';
import React from 'react';

interface TutorialStep {
  step: string;
  lines: number[] | number;
}

interface FileTutorialProps {
  steps: TutorialStep[];
}

const FileTutorial: React.FC<FileTutorialProps> = ({ steps }) => {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="w-full h-full overflow-hidden mx-auto py-6 bg-zinc-900 rounded-2xl shadow-lg border border-zinc-800">
      <h2 className="text-2xl font-bold mb-6 px-6 text-purple-400">File Tutorial</h2>
      <ul className="custom-scrollbar space-y-4 px-6 pb-12 text-zinc-100 overflow-y-auto h-full">
        {steps.map((stepObj, index) => {
          const { step, lines } = stepObj;

          const lineDisplay = Array.isArray(lines)
            ? lines.join(', ')
            : typeof lines === 'number'
            ? `${lines}`
            : '—';

          return (
            <li key={index} className="leading-relaxed">
              <p className="text-sm text-purple-300 mb-1">Lines: {lineDisplay}</p>
              <p>{step}</p>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default FileTutorial;
