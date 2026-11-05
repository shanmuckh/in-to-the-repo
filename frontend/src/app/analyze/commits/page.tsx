'use client';

import { GridBackground } from '@/components/GridBackground';
import React, { useEffect, useState } from 'react';
import Loading from '@/components/Loading';
import { RecentCommits } from '@/components/Git/RecentCommits';
import { TopContributors } from '@/components/Git/TopContributors';
import { MostChangedFiles } from '@/components/Git/MostChangedFiles';
import { ProjectSummary } from '@/components/Git/ProjectSummary';
import { motion, AnimatePresence } from 'framer-motion';
import { GitAnalysis } from '@/types/git_analysis_type';
import { Analysis } from '@/types/repo_analysis_type';
import axios from 'axios';
import { getAnalysisByIdRoute } from '@/utils/APIRoutes';

function Commits() {
  const [analysis, setAnalysis] = useState<GitAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("Retrieving git analysis...");

  useEffect(() => {
    async function fetchGitAnalysis() {
      setLoading(true);
      
      // Get repo_analysis_id from session
      const repoAnalysisId = sessionStorage.getItem('currentRepoAnalysisId');
      if (!repoAnalysisId) {
        setMessage("No analysis ID found.");
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

        setAnalysis(analysisData.git_analysis);
      } catch (err) {
        console.error("[COMMITS] Error fetching git analysis:", err);
        setMessage("Failed to load git analysis.");
      } finally {
        setLoading(false);
      }
    }
    fetchGitAnalysis();
  }, []);

  return (
    <div className="h-full w-full flex flex-col items-center relative overflow-y-scroll scroll-smooth">
      <div className="fixed h-screen w-full">
      <GridBackground />
      </div>

      {/* Heading */}
      <motion.h1
        className="relative text-xl w-full text-left p-10 lg:text-3xl z-20 font-bold bg-clip-text text-transparent bg-gradient-to-b from-neutral-50 to-neutral-400 bg-opacity-50"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <span className="relative bg-clip-text text-transparent bg-no-repeat bg-gradient-to-r from-purple-500 via-violet-500 to-pink-500 py-4">
          Git Analysis
        </span>
      </motion.h1>

      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="absolute inset-0 flex justify-center items-center z-30 bg-black bg-opacity-50"
          >
            <Loading message={message} />
          </motion.div>
        ) : (
          <motion.div
            key="analysis"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="flex flex-col h-full justify-center p-8 pt-0 w-[100%] lg:w-[80%] gap-4  z-10"
          >
            <motion.div
              className="h-full lg:h-[16rem] flex flex-col lg:flex-row justify-center gap-4 w-full items-center"
              initial="hidden"
              animate="visible"
              variants={{
                hidden: { opacity: 0, y: 30 },
                visible: { opacity: 1, y: 0, transition: { staggerChildren: 0.2 } }
              }}
            >
              {analysis && (
                <motion.div className="z-20 flex-2 w-full h-full" variants={{ hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0 } }}>
                  <ProjectSummary
                    repo={analysis.repo}
                    total_commits={analysis.total_commits_fetched}
                    first_commit_date={analysis.first_commit_date}
                    last_commit_date={analysis.last_commit_date}
                    owner={analysis.owner}
                    branch={analysis.default_branch}
                    description={analysis.description}
                  />
                </motion.div>
              )}

              {analysis && analysis?.top_contributors?.length > 0 && (
                <motion.div className="z-20 h-full flex-1 w-full" variants={{ hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0 } }}>
                  <TopContributors total_commits={analysis.total_commits_fetched} contributors={analysis.top_contributors} />
                </motion.div>
              )}

              {analysis && analysis?.most_changed_files?.length > 0 && (
                <motion.div className="z-20 h-full flex-2 w-full" variants={{ hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0 } }}>
                  <MostChangedFiles total_commits={analysis.total_commits_fetched} files={analysis.most_changed_files} />
                </motion.div>
              )}
            </motion.div>

            {analysis && analysis?.recent_commits?.length > 0 && (
              <motion.div
                className="z-20 h-[24rem] w-full"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3, duration: 0.6 }}
              >
                <RecentCommits recent_commits={analysis.recent_commits} />
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default Commits;
