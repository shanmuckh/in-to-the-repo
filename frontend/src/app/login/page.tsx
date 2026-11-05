"use client";
import React, { useState } from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { GridBackground } from "@/components/GridBackground";
import { loginRoute } from "@/utils/APIRoutes";
import { setAuthToken } from "@/utils/auth";
import axios, { AxiosError } from "axios";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await axios.post(loginRoute, formData);
      
      if (response.data.access_token) {
        setAuthToken(response.data.access_token);
        window.location.href = "/";
      }
    } catch (err: unknown) {
      const axiosError = err as AxiosError<{ detail: string }>;
      const errorMessage = axiosError.response?.data?.detail || "Login failed. Please check your credentials.";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen w-full items-center justify-center">
      <div className="fixed h-screen w-full">
        <GridBackground />
      </div>

      <div className="relative z-10 mx-auto w-full max-w-md rounded-2xl border border-neutral-800 bg-black p-4 shadow-2xl md:p-8">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-400 via-violet-400 to-pink-400 bg-clip-text text-transparent">
          Welcome back
        </h2>
        <p className="mt-2 max-w-sm text-sm text-neutral-400">
          Log in to access AI-powered features and your analysis history
        </p>

        {error && (
          <div className="mt-4 rounded-md bg-red-900/20 border border-red-500/50 p-3 text-sm text-red-400">
            {error}
          </div>
        )}

        <form className="my-8" onSubmit={handleSubmit}>
          <LabelInputContainer className="mb-4">
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              placeholder="you@example.com"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              disabled={loading}
            />
          </LabelInputContainer>

          <LabelInputContainer className="mb-8">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              placeholder="••••••••"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              disabled={loading}
            />
          </LabelInputContainer>

          <button
            className="shadow-[inset_0_0_0_2px_#616467] w-full text-white px-12 py-4 rounded-full tracking-widest uppercase font-bold bg-transparent hover:bg-[#616467] hover:text-white dark:text-neutral-200 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            type="submit"
            disabled={loading}
          >
            {loading ? "Logging in..." : "Log in"}
          </button>

          <div className="mt-6 text-center text-sm text-neutral-400">
            Don&apos;t have an account?{" "}
            <a href="/signup" className="text-purple-400 hover:text-purple-300 font-medium">
              Sign up
            </a>
          </div>
        </form>
      </div>
    </div>
  );
}

const LabelInputContainer = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => {
  return (
    <div className={cn("flex w-full flex-col space-y-2", className)}>
      {children}
    </div>
  );
};
