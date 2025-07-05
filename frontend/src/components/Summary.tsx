import React, { useState, useEffect } from 'react'

interface Message {
  id: string
  text: string
  sender: 'user' | 'agent'
  timestamp: Date
}

interface SummaryProps {
  summaryData: any
  messages: Message[]
}

const Summary: React.FC<SummaryProps> = ({ summaryData, messages }) => {
  const [htmlSummary, setHtmlSummary] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)

  const generateSummary = async () => {
    if (messages.length === 0) return

    setIsLoading(true)
    try {
      const conversationText = messages.map(msg => `${msg.sender}: ${msg.text}`).join('\n')
      
      const response = await fetch('http://localhost:8000/generate-summary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: conversationText
        })
      })

      if (response.ok) {
        const data = await response.json()
        setHtmlSummary(data.html_summary)
      }
    } catch (error) {
      console.error('Error generating summary:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    generateSummary()
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="h-full flex flex-col">
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900">Conversation Summary</h3>
          <p className="text-sm text-gray-600">Key information extracted from the chat</p>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center h-64 text-gray-500">
          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p className="text-center">Start a conversation to see the summary</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h3 className="text-lg font-semibold text-gray-900">Conversation Summary</h3>
        <p className="text-sm text-gray-600">AI-generated lending analysis</p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Generating summary...</span>
          </div>
        ) : htmlSummary ? (
          <div 
            className="p-6"
            dangerouslySetInnerHTML={{ __html: htmlSummary }}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>No summary available</p>
          </div>
        )}
      </div>

      {messages.length > 0 && (
        <div className="bg-white border-t border-gray-200 p-4 space-y-2">
          <button 
            onClick={generateSummary}
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors text-sm disabled:opacity-50"
          >
            {isLoading ? 'Generating...' : 'Refresh Summary'}
          </button>
        </div>
      )}
    </div>
  )
}

export default Summary