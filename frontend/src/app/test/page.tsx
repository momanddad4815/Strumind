'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { authAPI, projectsAPI, modelsAPI, analysisAPI } from '@/lib/api'
import { useAuthStore } from '@/store/auth'

export default function TestPage() {
  const { user, isAuthenticated } = useAuthStore()
  const [testResults, setTestResults] = useState<any>({})
  const [isRunningTests, setIsRunningTests] = useState(false)

  const runAPITests = async () => {
    setIsRunningTests(true)
    const results: any = {}

    try {
      // Test 1: Check if user is authenticated
      results.auth = {
        status: isAuthenticated ? 'PASS' : 'FAIL',
        message: isAuthenticated ? `Logged in as ${user?.name}` : 'Not authenticated',
        user: user
      }

      if (isAuthenticated) {
        // Test 2: Get projects
        try {
          const projects = await projectsAPI.getProjects()
          results.projects = {
            status: 'PASS',
            message: `Found ${projects.length} projects`,
            data: projects
          }

          // Test 3: Create a test project
          try {
            const newProject = await projectsAPI.createProject({
              name: 'Test Project',
              description: 'Created by API test'
            })
            results.createProject = {
              status: 'PASS',
              message: `Created project: ${newProject.name}`,
              data: newProject
            }

            // Test 4: Get models for the project
            try {
              const models = await modelsAPI.getModels(newProject.id)
              results.models = {
                status: 'PASS',
                message: `Found ${models.length} models`,
                data: models
              }

              // Test 5: Create a test model
              try {
                const newModel = await modelsAPI.createModel(newProject.id, {
                  name: 'Test Model',
                  description: 'Created by API test',
                  units: 'm'
                })
                results.createModel = {
                  status: 'PASS',
                  message: `Created model: ${newModel.name}`,
                  data: newModel
                }

                // Test 6: Run analysis
                try {
                  const analysisJob = await analysisAPI.runAnalysis(newProject.id, newModel.id, 'linear')
                  results.analysis = {
                    status: 'PASS',
                    message: `Started analysis job: ${analysisJob.job_id}`,
                    data: analysisJob
                  }

                  // Test 7: Check analysis status
                  setTimeout(async () => {
                    try {
                      const analysisStatus = await analysisAPI.getAnalysisStatus(analysisJob.job_id)
                      results.analysisStatus = {
                        status: 'PASS',
                        message: `Analysis status: ${analysisStatus.status}`,
                        data: analysisStatus
                      }
                      setTestResults({ ...results })
                    } catch (error) {
                      results.analysisStatus = {
                        status: 'FAIL',
                        message: `Analysis status error: ${error}`,
                        data: null
                      }
                      setTestResults({ ...results })
                    }
                  }, 2000)

                } catch (error) {
                  results.analysis = {
                    status: 'FAIL',
                    message: `Analysis error: ${error}`,
                    data: null
                  }
                }

              } catch (error) {
                results.createModel = {
                  status: 'FAIL',
                  message: `Create model error: ${error}`,
                  data: null
                }
              }

            } catch (error) {
              results.models = {
                status: 'FAIL',
                message: `Get models error: ${error}`,
                data: null
              }
            }

          } catch (error) {
            results.createProject = {
              status: 'FAIL',
              message: `Create project error: ${error}`,
              data: null
            }
          }

        } catch (error) {
          results.projects = {
            status: 'FAIL',
            message: `Get projects error: ${error}`,
            data: null
          }
        }
      }

    } catch (error) {
      results.error = {
        status: 'FAIL',
        message: `General error: ${error}`,
        data: null
      }
    }

    setTestResults(results)
    setIsRunningTests(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            StruMind API Test Suite
          </h1>
          <p className="text-gray-600 mb-6">
            Test all backend APIs and frontend-backend integration
          </p>
          
          <Button 
            onClick={runAPITests} 
            disabled={isRunningTests}
            className="mb-6"
          >
            {isRunningTests ? 'Running Tests...' : 'Run API Tests'}
          </Button>
        </div>

        <div className="space-y-4">
          {Object.entries(testResults).map(([testName, result]: [string, any]) => (
            <Card key={testName}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${
                    result.status === 'PASS' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  {testName.toUpperCase()}
                </CardTitle>
                <CardDescription>
                  {result.message}
                </CardDescription>
              </CardHeader>
              {result.data && (
                <CardContent>
                  <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-auto">
                    {JSON.stringify(result.data, null, 2)}
                  </pre>
                </CardContent>
              )}
            </Card>
          ))}
        </div>

        {Object.keys(testResults).length === 0 && (
          <Card>
            <CardContent className="p-8 text-center text-gray-500">
              Click "Run API Tests" to test all backend functionality
            </CardContent>
          </Card>
        )}

        <div className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle>Backend API Endpoints</CardTitle>
              <CardDescription>Available API endpoints in StruMind</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold mb-2">Authentication</h4>
                  <ul className="text-sm space-y-1 text-gray-600">
                    <li>• POST /api/auth/register</li>
                    <li>• POST /api/auth/login</li>
                    <li>• POST /api/auth/logout</li>
                    <li>• GET /api/auth/me</li>
                    <li>• POST /api/auth/forgot-password</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Projects</h4>
                  <ul className="text-sm space-y-1 text-gray-600">
                    <li>• GET /api/projects</li>
                    <li>• POST /api/projects</li>
                    <li>• GET /api/projects/{'{id}'}</li>
                    <li>• PUT /api/projects/{'{id}'}</li>
                    <li>• DELETE /api/projects/{'{id}'}</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Structural Models</h4>
                  <ul className="text-sm space-y-1 text-gray-600">
                    <li>• GET /api/projects/{'{id}'}/models</li>
                    <li>• POST /api/projects/{'{id}'}/models</li>
                    <li>• GET /api/projects/{'{id}'}/models/{'{id}'}</li>
                    <li>• PUT /api/projects/{'{id}'}/models/{'{id}'}</li>
                    <li>• DELETE /api/projects/{'{id}'}/models/{'{id}'}</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Analysis</h4>
                  <ul className="text-sm space-y-1 text-gray-600">
                    <li>• POST /api/projects/{'{id}'}/models/{'{id}'}/analysis</li>
                    <li>• GET /api/analysis/status/{'{job_id}'}</li>
                    <li>• GET /api/projects/{'{id}'}/models/{'{id}'}/results</li>
                    <li>• GET /api/materials</li>
                    <li>• GET /api/sections</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
