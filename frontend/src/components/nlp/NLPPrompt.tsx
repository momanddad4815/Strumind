'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { nlpAPI, nodesAPI, elementsAPI, NLPAction } from '@/lib/api'
import { MessageCircle, Send, Loader2, AlertCircle, CheckCircle } from 'lucide-react'

interface NLPPromptProps {
  projectId: number
  modelId: number
  onModelUpdate: () => void
}

export default function NLPPrompt({ projectId, modelId, onModelUpdate }: NLPPromptProps) {
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ message: string; success: boolean } | null>(null)
  const [showPrompt, setShowPrompt] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim()) return

    setLoading(true)
    setResult(null)

    try {
      const response = await nlpAPI.processPrompt(projectId, modelId, prompt)
      
      if (response.success) {
        // Process the actions
        await executeActions(response.actions)
        setResult({ message: response.message, success: true })
        onModelUpdate() // Refresh the model data
      } else {
        setResult({ message: response.message, success: false })
      }
    } catch (error) {
      console.error('Error processing NLP prompt:', error)
      setResult({ 
        message: 'An error occurred while processing your request. Please try again.', 
        success: false 
      })
    } finally {
      setLoading(false)
    }
  }

  const executeActions = async (actions: NLPAction[]) => {
    // Execute each action in sequence
    for (const action of actions) {
      if (action.action === 'create_node') {
        await nodesAPI.createNode(projectId, modelId, {
          label: action.params.label,
          position: action.params.position
        })
      } else if (action.action === 'create_element') {
        await elementsAPI.createElement(projectId, modelId, {
          label: action.params.label,
          type: action.params.type,
          start_node: action.params.start_node,
          end_node: action.params.end_node,
          material_id: 1, // Default material ID
          section_id: 1 // Default section ID
        })
      } else if (action.action === 'clear_model') {
        // This would require a special endpoint to clear the model
        // For now, we'll just refresh the model data
      }
    }
  }

  return (
    <div className="fixed bottom-4 right-4 z-10">
      {!showPrompt ? (
        <Button 
          onClick={() => setShowPrompt(true)}
          className="rounded-full h-12 w-12 p-0 shadow-lg"
        >
          <MessageCircle className="h-6 w-6" />
        </Button>
      ) : (
        <Card className="w-80 shadow-lg">
          <CardHeader className="pb-3">
            <div className="flex justify-between items-center">
              <CardTitle className="text-sm">Structural Assistant</CardTitle>
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-8 w-8 p-0"
                onClick={() => setShowPrompt(false)}
              >
                &times;
              </Button>
            </div>
            <CardDescription>
              Use natural language to create structures
            </CardDescription>
          </CardHeader>
          <CardContent>
            {result && (
              <div className={`mb-3 p-2 text-sm rounded ${
                result.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
              }`}>
                <div className="flex items-start">
                  {result.success ? (
                    <CheckCircle className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
                  )}
                  <span>{result.message}</span>
                </div>
              </div>
            )}
            
            <form onSubmit={handleSubmit} className="flex flex-col space-y-2">
              <div className="relative">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g., Create a 5-story building"
                  className="w-full p-2 pr-10 border rounded-md text-sm min-h-[80px] resize-none"
                  disabled={loading}
                />
                <Button
                  type="submit"
                  size="sm"
                  disabled={loading || !prompt.trim()}
                  className="absolute bottom-2 right-2 h-6 w-6 p-0 rounded-full"
                >
                  {loading ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Send className="h-3 w-3" />
                  )}
                </Button>
              </div>
              
              <div className="text-xs text-gray-500">
                <p>Try commands like:</p>
                <ul className="list-disc pl-4 mt-1 space-y-1">
                  <li>Create a 3-story building</li>
                  <li>Add a node at (5, 0, 3)</li>
                  <li>Create a frame with 3 bays and 2 stories</li>
                  <li>Create a truss with 5 segments</li>
                </ul>
              </div>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  )
}