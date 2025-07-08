import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Chatbot from './Chatbot'
import Summary from './Summary'
import CreditRequestSelector from './CreditRequestSelector'

interface Message {
  id: string
  text: string
  sender: 'user' | 'agent'
  timestamp: Date
}

const Chat = () => {
  const { chatId } = useParams<{ chatId: string }>()
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Message[]>([])
  const [summaryData, setSummaryData] = useState<any>(null)
  const [selectedRequestId, setSelectedRequestId] = useState<string>('')
  const [chatInputText, setChatInputText] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [isChatbotLoading, setIsChatbotLoading] = useState(false)

  // Generate new chatId if none provided
  useEffect(() => {
    if (!chatId) {
      const newChatId = generateChatId()
      navigate(`/${newChatId}`, { replace: true })
    }
  }, [chatId, navigate])

  // Load chat history when chatId changes
  useEffect(() => {
    if (chatId) {
      loadChatHistory(chatId)
    }
  }, [chatId])

  const generateChatId = (): string => {
    return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  }

  const loadChatHistory = async (chatId: string) => {
    setIsLoading(true)
    try {
      const response = await fetch(`http://localhost:8000/chat-history/${chatId}`)
      if (response.ok) {
        const data = await response.json()
        if (data.messages) {
          setMessages(data.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          })))
        }
        if (data.summaryData) {
          setSummaryData(data.summaryData)
        }
        if (data.selectedRequestId) {
          setSelectedRequestId(data.selectedRequestId)
        }
      } else if (response.status === 404) {
        // Chat doesn't exist yet, start fresh
        setMessages([])
        setSummaryData(null)
        setSelectedRequestId('')
      }
    } catch (error) {
      console.error('Error loading chat history:', error)
      // Start fresh on error
      setMessages([])
      setSummaryData(null)
      setSelectedRequestId('')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSectionClick = (sectionName: string) => {
    setChatInputText(`Continue working on ${sectionName}`)
  }

  if (!chatId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Creating new chat session...</p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading chat session...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-full mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Agentic Lender</h1>
              <p className="text-sm text-gray-600">AI-Powered Lending Assistant • Chat ID: {chatId}</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => {
                  const newChatId = generateChatId()
                  navigate(`/${newChatId}`)
                }}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
              >
                New Chat
              </button>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-gray-600">Online</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - Split Layout */}
      <main className="flex h-[calc(100vh-80px)]">
        {/* Left Side - Credit Request Selector and Chatbot */}
        <div className="w-1/2 border-r border-gray-200 bg-white flex flex-col h-full">
          <div className="p-4 border-b border-gray-200 flex-shrink-0">
            <CreditRequestSelector 
              onSelectRequest={setSelectedRequestId}
            />
          </div>
          <div className="flex-1 overflow-hidden">
            <Chatbot 
              messages={messages} 
              setMessages={setMessages}
              setSummaryData={setSummaryData}
              selectedRequestId={selectedRequestId}
              externalInputText={chatInputText}
              onInputTextChange={setChatInputText}
              chatId={chatId}
              setIsChatbotLoading={setIsChatbotLoading}
            />
          </div>
        </div>
        
        {/* Right Side - Summary */}
        <div className="w-1/2 bg-gray-50 h-full">
          <Summary summaryData={summaryData} messages={messages} onSectionClick={handleSectionClick} isChatbotLoading={isChatbotLoading} />
        </div>
      </main>
    </div>
  )
}

export default Chat