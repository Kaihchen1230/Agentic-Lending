import { Routes, Route, Navigate } from 'react-router-dom'
import Chat from './components/Chat'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to={`/chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`} replace />} />
      <Route path="/:chatId" element={<Chat />} />
    </Routes>
  )
}

export default App