import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authAPI, type User, type LoginData, type RegisterData } from '@/lib/api'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  // Actions
  login: (data: LoginData) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  clearError: () => void
  checkAuth: () => Promise<void>
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (data: LoginData) => {
        try {
          set({ isLoading: true, error: null })
          
          const response = await authAPI.login(data)
          
          // Store token in localStorage
          localStorage.setItem('auth_token', response.access_token)
          localStorage.setItem('user_data', JSON.stringify(response.user))
          
          set({
            user: response.user,
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null
          })
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Login failed'
          set({ 
            error: errorMessage, 
            isLoading: false,
            isAuthenticated: false,
            user: null,
            token: null
          })
          throw error
        }
      },

      register: async (data: RegisterData) => {
        try {
          set({ isLoading: true, error: null })
          
          const response = await authAPI.register(data)
          
          // Store token in localStorage
          localStorage.setItem('auth_token', response.access_token)
          localStorage.setItem('user_data', JSON.stringify(response.user))
          
          set({
            user: response.user,
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null
          })
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Registration failed'
          set({ 
            error: errorMessage, 
            isLoading: false,
            isAuthenticated: false,
            user: null,
            token: null
          })
          throw error
        }
      },

      logout: () => {
        // Clear localStorage
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_data')
        
        // Call logout API (fire and forget)
        authAPI.logout().catch(() => {})
        
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null
        })
      },

      clearError: () => {
        set({ error: null })
      },

      checkAuth: async () => {
        try {
          const token = localStorage.getItem('auth_token')
          const userData = localStorage.getItem('user_data')
          
          if (!token || !userData) {
            set({ isAuthenticated: false, user: null, token: null })
            return
          }

          // Verify token is still valid
          const user = await authAPI.me()
          
          set({
            user,
            token,
            isAuthenticated: true,
            error: null
          })
        } catch (error) {
          // Token is invalid, clear auth state
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user_data')
          
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            error: null
          })
        }
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading })
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
