import { useState } from 'react'
import Chatbot from './components/Chatbot'
import Summary from './components/Summary'

interface Message {
  id: string
  text: string
  sender: 'user' | 'agent'
  timestamp: Date
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [summaryData, setSummaryData] = useState<any>(null)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-full mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Agentic Lender</h1>
              <p className="text-sm text-gray-600">AI-Powered Lending Assistant</p>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Online</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - Split Layout */}
      <main className="flex h-[calc(100vh-80px)]">
        {/* Left Side - Chatbot */}
        <div className="w-1/2 border-r border-gray-200 bg-white">
          <Chatbot 
            messages={messages} 
            setMessages={setMessages}
            setSummaryData={setSummaryData}
          />
        </div>
        
        {/* Right Side - Summary */}
        <div className="w-1/2 bg-gray-50">
          <Summary summaryData={summaryData} messages={messages} />
        </div>
      </main>
    </div>
  )
}

export default App