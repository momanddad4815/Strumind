'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import StructuralViewer from '@/components/viewer/StructuralViewer'
import { projectsAPI, modelsAPI, nodesAPI, elementsAPI, Project, StructuralModel } from '@/lib/api'
import { Building2, ArrowLeft, Plus, Calculator, FileText, Download, Settings } from 'lucide-react'

export default function ModelDetailPage({ 
  params 
}: { 
  params: { projectId: string; modelId: string } 
}) {
  const router = useRouter()
  const projectId = parseInt(params.projectId)
  const modelId = parseInt(params.modelId)
  
  const [project, setProject] = useState<Project | null>(null)
  const [model, setModel] = useState<StructuralModel | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedElement, setSelectedElement] = useState<number | null>(null)
  const [selectedNode, setSelectedNode] = useState<number | null>(null)
  const [showDeformed, setShowDeformed] = useState(false)
  const [showLabels, setShowLabels] = useState(true)
  const [showNodeForm, setShowNodeForm] = useState(false)
  const [showElementForm, setShowElementForm] = useState(false)
  const [newNode, setNewNode] = useState({ label: '', position: [0, 0, 0] })
  const [newElement, setNewElement] = useState({ 
    label: '', 
    type: 'beam', 
    start_node: 0, 
    end_node: 0, 
    material_type: 'concrete', 
    section_id: 1 
  })

  useEffect(() => {
    if (isNaN(projectId) || isNaN(modelId)) {
      router.push('/projects')
      return
    }
    
    fetchProjectAndModel()
  }, [projectId, modelId])

  const fetchProjectAndModel = async () => {
    try {
      setLoading(true)
      const projectData = await projectsAPI.getProject(projectId)
      setProject(projectData)
      
      const modelData = await modelsAPI.getModel(projectId, modelId)
      setModel(modelData)
    } catch (error) {
      console.error('Failed to fetch model data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleElementClick = (elementId: number) => {
    setSelectedElement(elementId)
    setSelectedNode(null)
  }

  const handleNodeClick = (nodeId: number) => {
    setSelectedNode(nodeId)
    setSelectedElement(null)
  }

  const handleAddNode = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!model) return

    try {
      // Call the API to create a new node
      const nodeData = {
        label: newNode.label,
        position: newNode.position as [number, number, number],
        boundary_conditions: {
          fx: false, fy: false, fz: false,
          mx: false, my: false, mz: false
        }
      }
      
      const createdNode = await nodesAPI.createNode(projectId, modelId, nodeData)
      
      // Update the model with the new node
      const updatedModel = {
        ...model,
        nodes: [...model.nodes, createdNode]
      }
      
      setModel(updatedModel)
      setNewNode({ label: '', position: [0, 0, 0] })
      setShowNodeForm(false)
    } catch (error) {
      console.error('Failed to add node:', error)
    }
  }

  const handleAddElement = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!model) return

    try {
      // Call the API to create a new element
      const elementData = {
        label: newElement.label,
        type: newElement.type,
        start_node: newElement.start_node,
        end_node: newElement.end_node,
        material_id: 1, // Default material ID
        section_id: newElement.section_id
      }
      
      const createdElement = await elementsAPI.createElement(projectId, modelId, elementData)
      
      // Add material_type for rendering (this would normally come from the API)
      const elementToAdd = {
        ...createdElement,
        material_type: newElement.material_type
      }
      
      // Update the model with the new element
      const updatedModel = {
        ...model,
        elements: [...model.elements, elementToAdd]
      }
      
      setModel(updatedModel)
      setNewElement({ 
        label: '', 
        type: 'beam', 
        start_node: 0, 
        end_node: 0, 
        material_type: 'concrete', 
        section_id: 1 
      })
      setShowElementForm(false)
    } catch (error) {
      console.error('Failed to add element:', error)
    }
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
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm">
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </Button>
                <Button variant="outline" size="sm">
                  <FileText className="h-4 w-4 mr-2" />
                  Reports
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
              </div>
            </div>
          </div>
        </header>

        {loading ? (
          <div className="text-center py-10">
            <div className="spinner mb-4"></div>
            <p>Loading model data...</p>
          </div>
        ) : (
          <div className="flex h-[calc(100vh-80px)]">
            {/* Left Sidebar */}
            <div className="w-80 bg-white border-r flex flex-col">
              <div className="p-4 border-b">
                <Button variant="outline" onClick={() => router.push(`/projects/${projectId}`)} className="mb-4 w-full justify-start">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Project
                </Button>
                <h2 className="text-lg font-semibold text-gray-900">{model?.name || 'Model'}</h2>
                <p className="text-sm text-gray-500">{project?.name || 'Project'}</p>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Model Stats */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Model Statistics</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Nodes:</span>
                      <span className="font-medium">{model?.nodes?.length || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Elements:</span>
                      <span className="font-medium">{model?.elements?.length || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Materials:</span>
                      <span className="font-medium">{model?.materials?.length || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Units:</span>
                      <span className="font-medium">{model?.units || 'm'}</span>
                    </div>
                  </CardContent>
                </Card>

                {/* Quick Actions */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Model Actions</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <Button 
                      className="w-full justify-start" 
                      size="sm"
                      onClick={() => setShowNodeForm(true)}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add Node
                    </Button>
                    <Button 
                      className="w-full justify-start" 
                      size="sm"
                      onClick={() => setShowElementForm(true)}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add Element
                    </Button>
                    <Button className="w-full justify-start" size="sm">
                      <Calculator className="h-4 w-4 mr-2" />
                      Run Analysis
                    </Button>
                  </CardContent>
                </Card>

                {/* Viewer Controls */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Viewer Controls</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <label className="text-sm text-gray-600">Show Labels</label>
                      <input
                        type="checkbox"
                        checked={showLabels}
                        onChange={(e) => setShowLabels(e.target.checked)}
                        className="rounded"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-sm text-gray-600">Deformed Shape</label>
                      <input
                        type="checkbox"
                        checked={showDeformed}
                        onChange={(e) => setShowDeformed(e.target.checked)}
                        className="rounded"
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Selection Info */}
                {(selectedElement || selectedNode) && model && (
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Selection Details</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {selectedElement && (
                        <div className="space-y-2">
                          <div className="text-sm">
                            <span className="text-gray-600">Element:</span>
                            <span className="ml-2 font-medium">
                              {model.elements.find(e => e.id === selectedElement)?.label}
                            </span>
                          </div>
                          <div className="text-sm">
                            <span className="text-gray-600">Type:</span>
                            <span className="ml-2 font-medium">
                              {model.elements.find(e => e.id === selectedElement)?.type}
                            </span>
                          </div>
                          <div className="text-sm">
                            <span className="text-gray-600">Material:</span>
                            <span className="ml-2 font-medium">
                              {model.elements.find(e => e.id === selectedElement)?.material_type}
                            </span>
                          </div>
                        </div>
                      )}
                      {selectedNode && (
                        <div className="space-y-2">
                          <div className="text-sm">
                            <span className="text-gray-600">Node:</span>
                            <span className="ml-2 font-medium">
                              {model.nodes.find(n => n.id === selectedNode)?.label}
                            </span>
                          </div>
                          <div className="text-sm">
                            <span className="text-gray-600">Position:</span>
                            <span className="ml-2 font-medium">
                              ({model.nodes.find(n => n.id === selectedNode)?.position.join(', ')})
                            </span>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>

            {/* Main Content Area - 3D Viewer */}
            <div className="flex-1 relative">
              {model && (
                <StructuralViewer
                  model={model}
                  showNodes={true}
                  showElements={true}
                  showLabels={showLabels}
                  showDeformed={showDeformed}
                  colorByMaterial={true}
                  onElementClick={handleElementClick}
                  onNodeClick={handleNodeClick}
                />
              )}

              {/* Node Form Modal */}
              {showNodeForm && (
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
                  <Card className="w-full max-w-md">
                    <CardHeader>
                      <CardTitle>Add New Node</CardTitle>
                      <CardDescription>Enter the details for the new node</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <form onSubmit={handleAddNode} className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Node Label</label>
                          <input
                            type="text"
                            value={newNode.label}
                            onChange={(e) => setNewNode({ ...newNode, label: e.target.value })}
                            className="w-full p-2 border rounded-md"
                            placeholder="e.g., N1"
                            required
                          />
                        </div>
                        <div className="grid grid-cols-3 gap-2">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">X Position</label>
                            <input
                              type="number"
                              value={newNode.position[0]}
                              onChange={(e) => setNewNode({ 
                                ...newNode, 
                                position: [parseFloat(e.target.value), newNode.position[1], newNode.position[2]] 
                              })}
                              className="w-full p-2 border rounded-md"
                              step="0.1"
                              required
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Y Position</label>
                            <input
                              type="number"
                              value={newNode.position[1]}
                              onChange={(e) => setNewNode({ 
                                ...newNode, 
                                position: [newNode.position[0], parseFloat(e.target.value), newNode.position[2]] 
                              })}
                              className="w-full p-2 border rounded-md"
                              step="0.1"
                              required
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Z Position</label>
                            <input
                              type="number"
                              value={newNode.position[2]}
                              onChange={(e) => setNewNode({ 
                                ...newNode, 
                                position: [newNode.position[0], newNode.position[1], parseFloat(e.target.value)] 
                              })}
                              className="w-full p-2 border rounded-md"
                              step="0.1"
                              required
                            />
                          </div>
                        </div>
                        <div className="flex justify-end space-x-2 pt-2">
                          <Button type="button" variant="outline" onClick={() => setShowNodeForm(false)}>
                            Cancel
                          </Button>
                          <Button type="submit">
                            Add Node
                          </Button>
                        </div>
                      </form>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Element Form Modal */}
              {showElementForm && model && (
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
                  <Card className="w-full max-w-md">
                    <CardHeader>
                      <CardTitle>Add New Element</CardTitle>
                      <CardDescription>Enter the details for the new structural element</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <form onSubmit={handleAddElement} className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Element Label</label>
                          <input
                            type="text"
                            value={newElement.label}
                            onChange={(e) => setNewElement({ ...newElement, label: e.target.value })}
                            className="w-full p-2 border rounded-md"
                            placeholder="e.g., B1"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Element Type</label>
                          <select
                            value={newElement.type}
                            onChange={(e) => setNewElement({ ...newElement, type: e.target.value })}
                            className="w-full p-2 border rounded-md"
                            required
                          >
                            <option value="beam">Beam</option>
                            <option value="column">Column</option>
                            <option value="brace">Brace</option>
                          </select>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Start Node</label>
                            <select
                              value={newElement.start_node}
                              onChange={(e) => setNewElement({ ...newElement, start_node: parseInt(e.target.value) })}
                              className="w-full p-2 border rounded-md"
                              required
                            >
                              <option value="0">Select a node</option>
                              {model.nodes.map(node => (
                                <option key={node.id} value={node.id}>
                                  {node.label} ({node.position.join(', ')})
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">End Node</label>
                            <select
                              value={newElement.end_node}
                              onChange={(e) => setNewElement({ ...newElement, end_node: parseInt(e.target.value) })}
                              className="w-full p-2 border rounded-md"
                              required
                            >
                              <option value="0">Select a node</option>
                              {model.nodes.map(node => (
                                <option key={node.id} value={node.id}>
                                  {node.label} ({node.position.join(', ')})
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Material Type</label>
                          <select
                            value={newElement.material_type}
                            onChange={(e) => setNewElement({ ...newElement, material_type: e.target.value })}
                            className="w-full p-2 border rounded-md"
                            required
                          >
                            <option value="concrete">Concrete</option>
                            <option value="steel">Steel</option>
                            <option value="timber">Timber</option>
                            <option value="composite">Composite</option>
                          </select>
                        </div>
                        <div className="flex justify-end space-x-2 pt-2">
                          <Button type="button" variant="outline" onClick={() => setShowElementForm(false)}>
                            Cancel
                          </Button>
                          <Button type="submit">
                            Add Element
                          </Button>
                        </div>
                      </form>
                    </CardContent>
                  </Card>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  )
}