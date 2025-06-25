'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import StructuralViewer from '@/components/viewer/StructuralViewer'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { useAuthStore } from '@/store/auth'
import { Building2, Calculator, FileText, Download, Play, Settings, LogOut, User } from 'lucide-react'

// Sample structural model data
const sampleModel = {
  nodes: [
    { id: 1, label: 'N1', position: [0, 0, 0] as [number, number, number] },
    { id: 2, label: 'N2', position: [5, 0, 0] as [number, number, number] },
    { id: 3, label: 'N3', position: [10, 0, 0] as [number, number, number] },
    { id: 4, label: 'N4', position: [0, 0, 3] as [number, number, number] },
    { id: 5, label: 'N5', position: [5, 0, 3] as [number, number, number] },
    { id: 6, label: 'N6', position: [10, 0, 3] as [number, number, number] },
  ],
  elements: [
    { id: 1, label: 'C1', type: 'column', start_node: 1, end_node: 4, material_type: 'concrete', section_id: 1 },
    { id: 2, label: 'C2', type: 'column', start_node: 2, end_node: 5, material_type: 'concrete', section_id: 1 },
    { id: 3, label: 'C3', type: 'column', start_node: 3, end_node: 6, material_type: 'concrete', section_id: 1 },
    { id: 4, label: 'B1', type: 'beam', start_node: 4, end_node: 5, material_type: 'concrete', section_id: 2 },
    { id: 5, label: 'B2', type: 'beam', start_node: 5, end_node: 6, material_type: 'concrete', section_id: 2 },
  ],
  materials: {
    1: { name: 'M25 Concrete', type: 'concrete', color: '#808080' },
    2: { name: 'Fe415 Steel', type: 'steel', color: '#b87333' }
  },
  analysis_results: {
    type: 'linear_static',
    displacements: {
      '4': { ux: 0.001, uy: 0, uz: -0.005 },
      '5': { ux: 0.002, uy: 0, uz: -0.008 },
      '6': { ux: 0.001, uy: 0, uz: -0.005 }
    }
  }
}

export default function DashboardPage() {
  const router = useRouter()
  const { user, logout } = useAuthStore()
  const [selectedElement, setSelectedElement] = useState<number | null>(null)
  const [selectedNode, setSelectedNode] = useState<number | null>(null)
  const [showDeformed, setShowDeformed] = useState(false)
  const [showLabels, setShowLabels] = useState(true)

  const handleLogout = () => {
    logout()
    router.push('/auth/login')
  }

  const handleElementClick = (elementId: number) => {
    setSelectedElement(elementId)
    setSelectedNode(null)
  }

  const handleNodeClick = (nodeId: number) => {
    setSelectedNode(nodeId)
    setSelectedElement(null)
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
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <User className="h-4 w-4" />
                <span>Welcome, {user?.name || 'User'}</span>
              </div>
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
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-80px)]">
        {/* Left Sidebar */}
        <div className="w-80 bg-white border-r flex flex-col">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Project Dashboard</h2>
            <p className="text-sm text-gray-500">Sample Structural Model</p>
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
                  <span className="font-medium">{sampleModel.nodes.length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Elements:</span>
                  <span className="font-medium">{sampleModel.elements.length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Materials:</span>
                  <span className="font-medium">{Object.keys(sampleModel.materials).length}</span>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button className="w-full justify-start" size="sm">
                  <Calculator className="h-4 w-4 mr-2" />
                  Run Analysis
                </Button>
                <Button variant="outline" className="w-full justify-start" size="sm">
                  <Building2 className="h-4 w-4 mr-2" />
                  Design Elements
                </Button>
                <Button variant="outline" className="w-full justify-start" size="sm">
                  <FileText className="h-4 w-4 mr-2" />
                  Generate Reports
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
            {(selectedElement || selectedNode) && (
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
                          {sampleModel.elements.find(e => e.id === selectedElement)?.label}
                        </span>
                      </div>
                      <div className="text-sm">
                        <span className="text-gray-600">Type:</span>
                        <span className="ml-2 font-medium">
                          {sampleModel.elements.find(e => e.id === selectedElement)?.type}
                        </span>
                      </div>
                      <div className="text-sm">
                        <span className="text-gray-600">Material:</span>
                        <span className="ml-2 font-medium">
                          {sampleModel.elements.find(e => e.id === selectedElement)?.material_type}
                        </span>
                      </div>
                    </div>
                  )}
                  {selectedNode && (
                    <div className="space-y-2">
                      <div className="text-sm">
                        <span className="text-gray-600">Node:</span>
                        <span className="ml-2 font-medium">
                          {sampleModel.nodes.find(n => n.id === selectedNode)?.label}
                        </span>
                      </div>
                      <div className="text-sm">
                        <span className="text-gray-600">Position:</span>
                        <span className="ml-2 font-medium">
                          ({sampleModel.nodes.find(n => n.id === selectedNode)?.position.join(', ')})
                        </span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Analysis Results */}
            {sampleModel.analysis_results && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Analysis Results</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="text-sm">
                      <span className="text-gray-600">Analysis Type:</span>
                      <span className="ml-2 font-medium">{sampleModel.analysis_results.type}</span>
                    </div>
                    <div className="text-sm">
                      <span className="text-green-600">✓ Analysis Complete</span>
                    </div>
                    <Button variant="outline" size="sm" className="w-full mt-2">
                      <FileText className="h-4 w-4 mr-2" />
                      View Results
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Main Content Area - 3D Viewer */}
        <div className="flex-1 relative">
          <StructuralViewer
            model={sampleModel}
            showNodes={true}
            showElements={true}
            showLabels={showLabels}
            showDeformed={showDeformed}
            colorByMaterial={true}
            onElementClick={handleElementClick}
            onNodeClick={handleNodeClick}
          />
        </div>

        {/* Right Panel */}
        <div className="w-80 bg-white border-l">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Properties</h2>
          </div>
          
          <div className="p-4 space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Recent Activity</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-sm">
                  <div className="font-medium">Analysis Completed</div>
                  <div className="text-gray-500">Linear static analysis - 2 minutes ago</div>
                </div>
                <div className="text-sm">
                  <div className="font-medium">Model Created</div>
                  <div className="text-gray-500">Simple frame structure - 1 hour ago</div>
                </div>
                <div className="text-sm">
                  <div className="font-medium">Project Started</div>
                  <div className="text-gray-500">New structural project - 2 hours ago</div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Design Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Analysis</span>
                  <span className="text-sm text-green-600 font-medium">✓ Complete</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Design</span>
                  <span className="text-sm text-yellow-600 font-medium">⚠ Pending</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Detailing</span>
                  <span className="text-sm text-gray-400 font-medium">- Not Started</span>
                </div>
                <Button size="sm" className="w-full mt-3">
                  <Play className="h-4 w-4 mr-2" />
                  Start Design
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
      </div>
    </ProtectedRoute>
  )
}
