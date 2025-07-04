import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Create axios instance with base configuration
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear invalid token
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_data')
        window.location.href = '/auth/login'
      }
    }
    return Promise.reject(error)
  }
)

// Auth API functions
export interface RegisterData {
  name: string
  email: string
  password: string
  company?: string
}

export interface LoginData {
  email: string
  password: string
}

export interface User {
  id: number
  name: string
  email: string
  company?: string
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export const authAPI = {
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await api.post('/api/auth/register', data)
    return response.data
  },

  async login(data: LoginData): Promise<AuthResponse> {
    const response = await api.post('/api/auth/login', data)
    return response.data
  },

  async logout(): Promise<void> {
    await api.post('/api/auth/logout')
  },

  async me(): Promise<User> {
    const response = await api.get('/api/auth/me')
    return response.data
  },

  async forgotPassword(email: string): Promise<{ message: string }> {
    const response = await api.post('/api/auth/forgot-password', { email })
    return response.data
  },

  async resetPassword(token: string, password: string): Promise<{ message: string }> {
    const response = await api.post('/api/auth/reset-password', { token, password })
    return response.data
  }
}

// Projects API
export interface Project {
  id: number
  name: string
  description?: string
  created_at: string
  updated_at: string
}

export const projectsAPI = {
  async getProjects(): Promise<Project[]> {
    const response = await api.get('/api/projects')
    return response.data
  },

  async createProject(data: { name: string; description?: string }): Promise<Project> {
    const response = await api.post('/api/projects', data)
    return response.data
  },

  async getProject(id: number): Promise<Project> {
    const response = await api.get(`/api/projects/${id}`)
    return response.data
  },

  async updateProject(id: number, data: { name?: string; description?: string }): Promise<Project> {
    const response = await api.put(`/api/projects/${id}`, data)
    return response.data
  },

  async deleteProject(id: number): Promise<void> {
    await api.delete(`/api/projects/${id}`)
  }
}

// Structural Models API
export interface Node {
  id: number
  label: string
  position: [number, number, number]
  boundary_conditions?: {
    fx: boolean
    fy: boolean
    fz: boolean
    mx: boolean
    my: boolean
    mz: boolean
  }
}

export interface Element {
  id: number
  label: string
  type: string
  start_node: number
  end_node: number
  material_id?: number
  section_id?: number
  material_type?: string
}

export interface Material {
  id: number
  name: string
  type: string
  properties: Record<string, number>
}

export interface StructuralModel {
  id: number
  project_id: number
  name: string
  description?: string
  units: string
  created_at: string
  updated_at: string
  nodes: Node[]
  elements: Element[]
  materials: any[]
  analysis_results?: any
}

export const modelsAPI = {
  async getModels(projectId: number): Promise<StructuralModel[]> {
    const response = await api.get(`/api/projects/${projectId}/models`)
    return response.data
  },

  async createModel(projectId: number, data: { name: string; description?: string; units?: string }): Promise<StructuralModel> {
    const response = await api.post(`/api/projects/${projectId}/models`, data)
    return response.data
  },

  async getModel(projectId: number, modelId: number): Promise<StructuralModel> {
    const response = await api.get(`/api/projects/${projectId}/models/${modelId}`)
    return response.data
  },

  async updateModel(projectId: number, modelId: number, data: any): Promise<StructuralModel> {
    const response = await api.put(`/api/projects/${projectId}/models/${modelId}`, data)
    return response.data
  },

  async deleteModel(projectId: number, modelId: number): Promise<void> {
    await api.delete(`/api/projects/${projectId}/models/${modelId}`)
  }
}

// Nodes API
export const nodesAPI = {
  async getNodes(projectId: number, modelId: number): Promise<Node[]> {
    const response = await api.get(`/api/projects/${projectId}/models/${modelId}/nodes`)
    return response.data
  },

  async createNode(
    projectId: number, 
    modelId: number, 
    data: { 
      label: string; 
      position: [number, number, number]; 
      boundary_conditions?: Record<string, boolean> 
    }
  ): Promise<Node> {
    const response = await api.post(`/api/projects/${projectId}/models/${modelId}/nodes`, data)
    return response.data
  },

  async getNode(projectId: number, modelId: number, nodeId: number): Promise<Node> {
    const response = await api.get(`/api/projects/${projectId}/models/${modelId}/nodes/${nodeId}`)
    return response.data
  },

  async updateNode(
    projectId: number, 
    modelId: number, 
    nodeId: number, 
    data: { 
      label?: string; 
      position?: [number, number, number]; 
      boundary_conditions?: Record<string, boolean> 
    }
  ): Promise<Node> {
    const response = await api.put(`/api/projects/${projectId}/models/${modelId}/nodes/${nodeId}`, data)
    return response.data
  },

  async deleteNode(projectId: number, modelId: number, nodeId: number): Promise<void> {
    await api.delete(`/api/projects/${projectId}/models/${modelId}/nodes/${nodeId}`)
  }
}

// Elements API
export const elementsAPI = {
  async getElements(projectId: number, modelId: number): Promise<Element[]> {
    const response = await api.get(`/api/projects/${projectId}/models/${modelId}/elements`)
    return response.data
  },

  async createElement(
    projectId: number, 
    modelId: number, 
    data: { 
      label: string; 
      type: string;
      start_node: number;
      end_node: number;
      material_id?: number;
      section_id?: number;
    }
  ): Promise<Element> {
    const response = await api.post(`/api/projects/${projectId}/models/${modelId}/elements`, data)
    return response.data
  },

  async getElement(projectId: number, modelId: number, elementId: number): Promise<Element> {
    const response = await api.get(`/api/projects/${projectId}/models/${modelId}/elements/${elementId}`)
    return response.data
  },

  async updateElement(
    projectId: number, 
    modelId: number, 
    elementId: number, 
    data: { 
      label?: string; 
      type?: string;
      start_node?: number;
      end_node?: number;
      material_id?: number;
      section_id?: number;
    }
  ): Promise<Element> {
    const response = await api.put(`/api/projects/${projectId}/models/${modelId}/elements/${elementId}`, data)
    return response.data
  },

  async deleteElement(projectId: number, modelId: number, elementId: number): Promise<void> {
    await api.delete(`/api/projects/${projectId}/models/${modelId}/elements/${elementId}`)
  }
}

// Analysis API
export const analysisAPI = {
  async runAnalysis(projectId: number, modelId: number, analysisType: string): Promise<{ job_id: string }> {
    const response = await api.post(`/api/projects/${projectId}/models/${modelId}/analysis`, { 
      analysis_type: analysisType 
    })
    return response.data
  },

  async getAnalysisStatus(jobId: string): Promise<{ status: string; progress: number; result?: any }> {
    const response = await api.get(`/api/analysis/status/${jobId}`)
    return response.data
  },

  async getAnalysisResults(projectId: number, modelId: number): Promise<any> {
    const response = await api.get(`/api/projects/${projectId}/models/${modelId}/results`)
    return response.data
  }
}

// NLP API for natural language processing
export interface NLPAction {
  action: string
  params: Record<string, any>
}

export interface NLPResponse {
  actions: NLPAction[]
  message: string
  success: boolean
}

export const nlpAPI = {
  async processPrompt(projectId: number, modelId: number, prompt: string): Promise<NLPResponse> {
    const response = await api.post('/api/nlp/process', {
      prompt,
      project_id: projectId,
      model_id: modelId
    })
    return response.data
  }
}

export default api
