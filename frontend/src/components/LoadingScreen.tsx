"use client";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { Spotlight } from "@/components/ui/spotlight-new";
import { Cover } from "@/components/ui/cover";
import { host } from "@/utils/APIRoutes";

export default function LoadingScreen({ requestId }: { requestId: string }) {
  const [progressMessage, setProgressMessage] = useState("");
  const router = useRouter();

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const statusUrl = `${host}/api/analyze/status/${requestId}`;
        const response = await axios.get(statusUrl);
        const data = response.data;

        if (data.status === "in-progress") {
          setProgressMessage(data.progress || "Processing...");
        } else if (data.status === "pending") {
          setProgressMessage("Queued...");
        } else if (data.status === "completed") {
          clearInterval(pollingInterval);

          if (data.result?.repo_analysis_id) {
            router.push(`/analyze?id=${data.result.repo_analysis_id}`);
          } else {
            console.error("No repo_analysis_id in response. Result:", data.result);
            setProgressMessage("Analysis completed but could not retrieve ID. Please check history.");
          }
        } else if (data.status === "failed") {
          clearInterval(pollingInterval);
          console.error("Analysis failed", data);
          setProgressMessage(`Analysis failed: ${data.error || "Unknown error"}`);
        }
      } catch (error) {
        console.error("Error polling status:", error);
      }
    };

    pollStatus();

    const pollingInterval = setInterval(pollStatus, 2000);

    return () => {
      clearInterval(pollingInterval);
    };
  }, [requestId, router]);

  const firstSpaceIndex = progressMessage.indexOf(" ");
  const firstWord = firstSpaceIndex === -1 ? progressMessage : progressMessage.slice(0, firstSpaceIndex);
  const restOfMessage = firstSpaceIndex === -1 ? "" : progressMessage.slice(firstSpaceIndex);

  return (
    <div className="h-screen flex flex-col justify-center items-center bg-black relative overflow-hidden px-4">
      <Spotlight />
      <div className="text-center">
        <h1 className="text-2xl px-4 md:text-3xl lg:text-3xl font-semibold max-w-7xl mx-auto text-center mt-6 relative z-20 py-6 bg-clip-text text-transparent bg-linear-to-b from-neutral-800 via-neutral-700 to-neutral-700 dark:from-neutral-800 dark:via-white dark:to-white transition-opacity duration-500 ease-in-out">
          <Cover>{firstWord}</Cover>
          <span style={{ wordBreak: "break-word" }}>{restOfMessage}</span>
        </h1>
        {progressMessage.includes("Error") || progressMessage.includes("error") ? (
          <p className="text-red-500 mt-4">Something went wrong. Please try again.</p>
        ) : null}
      </div>
    </div>
  );
}