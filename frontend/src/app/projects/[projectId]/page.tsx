'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { projectsAPI, modelsAPI, Project, StructuralModel } from '@/lib/api'
import { Building2, Plus, Trash2, Edit, ArrowLeft, ArrowRight, Box, Cube } from 'lucide-react'

export default function ProjectDetailPage({ params }: { params: { projectId: string } }) {
  const router = useRouter()
  const projectId = parseInt(params.projectId)
  
  const [project, setProject] = useState<Project | null>(null)
  const [models, setModels] = useState<StructuralModel[]>([])
  const [loading, setLoading] = useState(true)
  const [newModel, setNewModel] = useState({ name: '', description: '', units: 'm' })
  const [showNewModelForm, setShowNewModelForm] = useState(false)

  useEffect(() => {
    if (isNaN(projectId)) {
      router.push('/projects')
      return
    }
    
    fetchProjectAndModels()
  }, [projectId])

  const fetchProjectAndModels = async () => {
    try {
      setLoading(true)
      const projectData = await projectsAPI.getProject(projectId)
      setProject(projectData)
      
      const modelsData = await modelsAPI.getModels(projectId)
      setModels(modelsData)
    } catch (error) {
      console.error('Failed to fetch project data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateModel = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const model = await modelsAPI.createModel(projectId, newModel)
      setModels([...models, model])
      setNewModel({ name: '', description: '', units: 'm' })
      setShowNewModelForm(false)
    } catch (error) {
      console.error('Failed to create model:', error)
    }
  }

  const handleDeleteModel = async (modelId: number) => {
    if (confirm('Are you sure you want to delete this model?')) {
      try {
        await modelsAPI.deleteModel(projectId, modelId)
        setModels(models.filter(m => m.id !== modelId))
      } catch (error) {
        console.error('Failed to delete model:', error)
      }
    }
  }

  const navigateToModel = (modelId: number) => {
    router.push(`/projects/${projectId}/models/${modelId}`)
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Building2 className="h-8 w-8 text-blue-600" />
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">StruMind</h1>
                  <p className="text-sm text-gray-500">Structural Engineering Platform</p>
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="container mx-auto py-8 px-4">
          <div className="flex items-center mb-6">
            <Button variant="outline" onClick={() => router.push('/projects')} className="mr-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Projects
            </Button>
            <h1 className="text-2xl font-bold text-gray-900">{project?.name || 'Project Details'}</h1>
          </div>

          {loading ? (
            <div className="text-center py-10">
              <div className="spinner mb-4"></div>
              <p>Loading project data...</p>
            </div>
          ) : (
            <>
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Project Information</CardTitle>
                  <CardDescription>
                    Created: {project ? new Date(project.created_at).toLocaleDateString() : ''}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4">
                    {project?.description || 'No description provided'}
                  </p>
                </CardContent>
              </Card>

              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900">Structural Models</h2>
                <Button onClick={() => setShowNewModelForm(!showNewModelForm)}>
                  <Plus className="h-4 w-4 mr-2" />
                  New Model
                </Button>
              </div>

              {showNewModelForm && (
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle>Create New Structural Model</CardTitle>
                    <CardDescription>Enter the details for your new structural model</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleCreateModel} className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Model Name</label>
                        <input
                          type="text"
                          value={newModel.name}
                          onChange={(e) => setNewModel({ ...newModel, name: e.target.value })}
                          className="w-full p-2 border rounded-md"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                        <textarea
                          value={newModel.description}
                          onChange={(e) => setNewModel({ ...newModel, description: e.target.value })}
                          className="w-full p-2 border rounded-md"
                          rows={3}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Units</label>
                        <select
                          value={newModel.units}
                          onChange={(e) => setNewModel({ ...newModel, units: e.target.value })}
                          className="w-full p-2 border rounded-md"
                        >
                          <option value="m">Meters (m)</option>
                          <option value="mm">Millimeters (mm)</option>
                          <option value="ft">Feet (ft)</option>
                          <option value="in">Inches (in)</option>
                        </select>
                      </div>
                      <div className="flex justify-end space-x-2">
                        <Button type="button" variant="outline" onClick={() => setShowNewModelForm(false)}>
                          Cancel
                        </Button>
                        <Button type="submit">
                          Create Model
                        </Button>
                      </div>
                    </form>
                  </CardContent>
                </Card>
              )}

              {models.length === 0 ? (
                <div className="text-center py-10 bg-white rounded-lg shadow">
                  <Cube className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Models Yet</h3>
                  <p className="text-gray-500 mb-4">Create your first structural model to get started</p>
                  <Button onClick={() => setShowNewModelForm(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Model
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {models.map((model) => (
                    <Card key={model.id} className="hover:shadow-md transition-shadow">
                      <CardHeader>
                        <CardTitle>{model.name}</CardTitle>
                        <CardDescription>
                          Units: {model.units} | Created: {new Date(model.created_at).toLocaleDateString()}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <p className="text-gray-600 mb-4 min-h-[60px]">
                          {model.description || 'No description provided'}
                        </p>
                        <div className="flex justify-between items-center mb-4">
                          <div className="text-sm text-gray-500">
                            <div>Nodes: {model.nodes?.length || 0}</div>
                            <div>Elements: {model.elements?.length || 0}</div>
                          </div>
                          <Box className="h-10 w-10 text-blue-500" />
                        </div>
                        <div className="flex justify-between">
                          <div className="space-x-2">
                            <Button variant="outline" size="sm" onClick={() => handleDeleteModel(model.id)}>
                              <Trash2 className="h-4 w-4 mr-1" />
                              Delete
                            </Button>
                            <Button variant="outline" size="sm">
                              <Edit className="h-4 w-4 mr-1" />
                              Edit
                            </Button>
                          </div>
                          <Button size="sm" onClick={() => navigateToModel(model.id)}>
                            Open
                            <ArrowRight className="h-4 w-4 ml-1" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </ProtectedRoute>
  )
}