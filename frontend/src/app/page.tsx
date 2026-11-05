"use client";
import React, { useState } from "react";
import { Spotlight } from "@/components/ui/spotlight-new";
import { Form } from "@/components/Form";
import LoadingScreen from "@/components/LoadingScreen";
import { UserMenu } from "@/components/UserMenu";



export default function Home() {
  const [loading, setLoading] = useState<boolean>(false);
  const [requestId, setRequestId] = useState<string>("")

  if (loading) {
    return (
      <LoadingScreen requestId={requestId} />
    )
  }

  return (
    <div className="h-screen w-full justify-center items-center  flex md:items-center md:justify-center bg-black  relative overflow-hidden">
      <Spotlight />

      {/* User Menu - Top Right */}
      <div className="absolute top-6 right-6 z-50">
        <UserMenu />
      </div>

      <div className="flex flex-col justify-center items-center gap-4 p-4 max-w-7xl  mx-auto relative z-10  w-full">
        <h1 className="text-5xl md:text-7xl font-bold text-center bg-clip-text text-transparent bg-linear-to-b from-neutral-50 to-neutral-400 bg-opacity-50">
          In to the <span className="relative bg-clip-text text-transparent bg-no-repeat bg-linear-to-r from-purple-500 via-violet-500 to-pink-500 py-4">repo</span>
        </h1>
        <p className="font-normal text-xl w-90 md:w-120 p-4 text-center text-neutral-300 ">
          {`A smarter way to explore codebases—because reading thousands of lines shouldn't feel like decoding ancient scripts.`}
        </p>
        <div className="w-90 md:w-100 ">
          <Form setParentRequestId={setRequestId} setParentLoading={setLoading} />
        </div>
      </div>
    </div>
  );
}
