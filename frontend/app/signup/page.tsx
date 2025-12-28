'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authAPI } from '@/lib/api-client';
import { useStore } from '@/lib/store';
import Link from 'next/link';

export default function SignupPage() {
  const router = useRouter();
  const { setAuth } = useStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.signup(
        email,
        password,
        fullName || undefined,
        username || undefined
      );
      
      if (response.status && response.data) {
        const { access_token, refresh_token, user_id, email, first_name, last_name, role, is_active } = response.data;
        
        if (!access_token || !refresh_token) {
          setError('Invalid response from server. Missing authentication tokens.');
          return;
        }
        
        // Store tokens
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
        }
        
        // Try to get current user, but if it fails, use data from signup response
        let userData;
        try {
          const userResponse = await authAPI.getCurrentUser();
          userData = userResponse.data;
        } catch (userError: any) {
          // If getCurrentUser fails, use the data from signup response
          console.warn('getCurrentUser failed, using signup response data:', userError);
          userData = {
            user_id,
            email,
            first_name,
            last_name,
            role,
            is_active,
            username: response.data.username || null,
            full_name: first_name && last_name ? `${first_name} ${last_name}` : (first_name || last_name || null),
            mobile: null
          };
        }
        
        setAuth(
          userData,
          access_token,
          refresh_token
        );
        
        router.push('/app');
      } else {
        setError(response.message || 'Signup failed. Invalid response from server.');
      }
    } catch (err: any) {
      // Log error to console for debugging (only in development)
      if (process.env.NODE_ENV === 'development') {
        console.error('Signup error:', err);
      }
      
      // Show user-friendly error message
      let errorMessage = 'Unable to create your account. Please try again.';
      
      if (err.response?.data?.detail) {
        // Use the error message from backend (already user-friendly)
        errorMessage = err.response.data.detail;
      } else if (err.response?.status === 0 || !err.response) {
        // Network error
        errorMessage = 'Unable to connect to the server. Please check your connection and try again.';
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">🧠 NotebookLM</h1>
          <p className="text-gray-400">Understand Anything</p>
        </div>

        <div className="bg-secondary rounded-lg p-8 shadow-lg">
          <h2 className="text-2xl font-bold mb-6">Create Account</h2>

          {error && (
            <div className="bg-primary/20 border border-primary/50 text-primary px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSignup} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-2">
                Email *
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium mb-2">
                Password *
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                className="w-full px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <p className="text-xs text-gray-400 mt-1">Must be at least 8 characters</p>
            </div>

            <div>
              <label htmlFor="fullName" className="block text-sm font-medium mb-2">
                Full Name
              </label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            <div>
              <label htmlFor="username" className="block text-sm font-medium mb-2">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary hover:bg-primary-hover text-white font-semibold py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating account...' : 'Sign Up'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-400">
              Already have an account?{' '}
              <Link href="/login" className="text-primary hover:underline">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

