"use client";
import React, { useEffect, useState } from "react";
import { isAuthenticated, removeAuthToken, getAuthHeaders } from "@/utils/auth";
import { userMeRoute } from "@/utils/APIRoutes";
import axios from "axios";
import { useRouter } from "next/navigation";

interface UserData {
  email: string;
  username: string;
  id: number;
}

export function UserMenu() {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchUser() {
      if (!isAuthenticated()) {
        setLoading(false);
        return;
      }

      try {
        const response = await axios.get(userMeRoute, {
          headers: getAuthHeaders(),
        });
        setUser(response.data);
      } catch (error) {
        console.error("Failed to fetch user:", error);
        // Token might be expired, remove it
        removeAuthToken();
      } finally {
        setLoading(false);
      }
    }

    fetchUser();
  }, []);

  const handleLogout = () => {
    removeAuthToken();
    setUser(null);
    router.push("/");
  };

  if (loading) {
    return null;
  }

  if (!user) {
    return (
      <div className="flex items-center gap-3">
        <a
          href="/login"
          className="text-sm text-neutral-300 hover:text-white transition-colors"
        >
          Log in
        </a>
        <a
          href="/signup"
          className="px-4 py-2 text-sm rounded-lg bg-gradient-to-r from-purple-500 via-violet-500 to-pink-500 text-white font-medium hover:opacity-90 transition-opacity"
        >
          Sign up
        </a>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 transition-colors"
      >
        <div className="h-8 w-8 rounded-full bg-gradient-to-r from-purple-500 via-violet-500 to-pink-500 flex items-center justify-center text-white font-semibold text-sm">
          {user.username.charAt(0).toUpperCase()}
        </div>
        <span className="text-sm text-white font-medium">{user.username}</span>
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-30"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-56 rounded-lg bg-neutral-900 border border-neutral-800 shadow-xl z-40 overflow-hidden">
            <div className="p-3 border-b border-neutral-800">
              <p className="text-sm font-medium text-white">{user.username}</p>
              <p className="text-xs text-neutral-400 truncate">{user.email}</p>
            </div>
            <div className="p-2">
              <a
                href="/history"
                className="block px-3 py-2 text-sm text-neutral-300 hover:bg-neutral-800 rounded-md transition-colors"
              >
                Analysis History
              </a>
              <button
                onClick={handleLogout}
                className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-neutral-800 rounded-md transition-colors"
              >
                Log out
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
