import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  full_name?: string;
  username?: string;
}

interface Source {
  name: string;
  type: string;
  chunks: number;
  uploaded_at?: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  timestamp: Date;
}

interface AppState {
  // Auth
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  
  // Sources
  sources: Source[];
  
  // Chat
  messages: Message[];
  currentSessionId: string | null;
  isLoading: boolean;
  
  // Actions
  setAuth: (user: User | null, accessToken: string | null, refreshToken: string | null) => void;
  logout: () => void;
  setSources: (sources: Source[]) => void;
  addSource: (source: Source) => void;
  removeSource: (sourceName: string) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  setLoading: (loading: boolean) => void;
  setSessionId: (sessionId: string | null) => void;
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      sources: [],
      messages: [],
      currentSessionId: null,
      isLoading: false,
      
      // Actions
      setAuth: (user, accessToken, refreshToken) => {
        if (typeof window !== 'undefined') {
          if (accessToken) localStorage.setItem('access_token', accessToken);
          if (refreshToken) localStorage.setItem('refresh_token', refreshToken);
        }
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: !!user && !!accessToken,
        });
      },
      
      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          messages: [],
          currentSessionId: null,
        });
      },
      
      setSources: (sources) => set({ sources }),
      addSource: (source) => set((state) => ({ sources: [...state.sources, source] })),
      removeSource: (sourceName) => set((state) => ({ 
        sources: state.sources.filter(s => s.name !== sourceName) 
      })),
      
      setMessages: (messages) => set({ messages }),
      addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
      
      setLoading: (isLoading) => set({ isLoading }),
      setSessionId: (sessionId) => set({ currentSessionId: sessionId }),
    }),
    {
      name: 'notebooklm-storage',
      storage: createJSONStorage(() => {
        if (typeof window !== 'undefined') {
          return localStorage;
        }
        // Fallback for SSR - return a no-op storage
        return {
          getItem: () => null,
          setItem: () => {},
          removeItem: () => {},
        };
      }),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        sources: state.sources,
        messages: state.messages,
        currentSessionId: state.currentSessionId,
      }),
    }
  )
);

