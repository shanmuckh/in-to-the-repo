'use client';

import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { GridBackground } from '@/components/GridBackground';
import Loading from '@/components/Loading';
import { PlaceholdersAndVanishInput } from '@/components/ui/placeholders-and-vanish-input';
import { askAssistantRoute } from '@/utils/APIRoutes';
import clsx from 'clsx';
import {motion} from "framer-motion"
import { FileAnalysis } from '@/types/file_analysis_type';
import FileSelector from '@/components/FileAnalysis/FileSelector';
import { getItem, setItem } from '@/utils/indexedDB';
import { getAuthHeaders, isAuthenticated } from '@/utils/auth';

function Assistant() {
  const [currentFile, setCurrentFile] = useState<string>('Choose a file to ask the assistant.');
  const [code, setCode] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('Preparing your assistant...');
  const [chat, setChat] = useState<{ role: string; content: string}[]>([]);
  const [input, setInput] = useState('');
  const [historyID, setHistoryID] = useState<string | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const chatRef = useRef<HTMLDivElement | null>(null);

useEffect(() => {
  async function fetchLastUsedFile() {
    try {
      const file = await getItem<string>('lastUsedFile');
      const storedHistoryID = await getItem<string>('history_id');

      if (storedHistoryID) {
        setHistoryID(storedHistoryID);
      }

      if (!file) {
        setMessage('No file selected. Please select a file from architecture map.');
        setLoading(false);
        return;
      }

      setCurrentFile(file);

      const fileAnalysis = await getItem<FileAnalysis>(`fileAnalysis-${file}`);
      if (fileAnalysis) {
        setCode(JSON.stringify(fileAnalysis.analysis.code));
      } else {
        setMessage('No analysis found for selected file.');
      }
    } catch (error) {
      setMessage('Failed to load file data. Please try again.');
      console.error(error);
    } finally {
      setLoading(false);
    }
  }
  fetchLastUsedFile();
}, []);



  // Scroll to bottom on new message
  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: 'smooth' });
  }, [chat]);

  const handleSubmit = async () => {
    if (!input.trim()) return;

    // Check if user is authenticated
    if (!isAuthenticated()) {
      setChat(prev => [
        ...prev,
        { role: 'user', content: input },
        {
          role: 'assistant',
          content: 'AI Assistant is only available to logged-in users. Please sign up or log in to use this feature.',
        },
      ]);
      setInput('');
      return;
    }

    const userMessage = { role: 'user', content: input };
    setChat(prev => [...prev, userMessage]);
    setInput('');
    setIsThinking(true);

    try {
      const res = await axios.post(askAssistantRoute, {
        question: input,
        code: code,
        history_id: historyID,
        reset: false,
      }, {
        headers: getAuthHeaders()
      });

      const data = res.data;



      if (!historyID && data.history_id) {
        await setItem('history_id',data.history_id)
        setHistoryID(data.history_id);
      }

      const assistantMessage = {
        role: 'assistant',
        content: data.answer || 'Sorry something went wrong. Please try again later.'
      };

      setChat(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      console.log(err)
      const errorMessage = err.response?.status === 401 
        ? 'Your session has expired. Please log in again to continue using AI features.'
        : 'Sorry, something went wrong. Please try again.';
      setChat(prev => [
        ...prev,
        {
          role: 'assistant',
          content: errorMessage,
        },
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  if (loading) return <Loading message={message} />;

  return (
    <div className="w-full h-screen flex flex-col relative overflow-hidden">
      <div className="fixed h-screen w-full">
        <GridBackground />
      </div>

      <motion.div
      initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
       className='w-full p-10 flex items-center'>
        {/* Heading */}
        <h1 className="relative text-xl pr-4  text-left lg:text-3xl z-20 font-bold bg-clip-text text-transparent bg-gradient-to-b from-neutral-50 to-neutral-400 bg-opacity-50">
          <span className="relative bg-clip-text text-transparent bg-no-repeat bg-gradient-to-r from-purple-500 via-violet-500 to-pink-500 py-4">
            Assistant:
          </span> 
        </h1>
        <FileSelector  selectedFile={currentFile} onFileSelect={()=>{window.location.reload()}}/>
      </motion.div>

<div className='fixed inset-x-0 bottom-20 top-[120px] flex flex-col items-center px-4 overflow-hidden'>
      {/* Chat History */}
      <div
        ref={chatRef}
        className="h-full rounded-xl  z-10 px-4 overflow-y-auto w-full max-w-3xl  mb-4 space-y-4 custom-scrollbar"
      >
        {chat.map((msg, index) => (
          <div
            key={index}
            className={clsx(
              'px-4 py-2 rounded-xl max-w-[80%] whitespace-pre-wrap break-words',
              msg.role === 'user'
                ? 'bg-no-repeat bg-gradient-to-r from-purple-500 via-violet-500 to-pink-500 text-white self-end ml-auto'
                : 'bg-neutral-200 text-black self-start'
            )}
          >
              {msg.content}
          </div>
        ))}

        {isThinking && (
          <div className="bg-neutral-200 text-black self-start px-4 py-2 rounded-xl max-w-[80%] animate-pulse">
            Thinking...
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-8 pt-0 w-full   lg:max-w-3xl  z-20">
        <PlaceholdersAndVanishInput
          placeholders={[`Ask something about ${currentFile}`]}
          onChange={e => setInput(e.target.value)}
          onSubmit={handleSubmit}
        />
      </div>
    </div>
    </div>
  );
}

export default Assistant;
