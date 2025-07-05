import React, { useState, useRef, useEffect } from 'react';

interface Message {
	id: string;
	text: string;
	sender: 'user' | 'agent';
	timestamp: Date;
}

interface ChatbotProps {
	messages: Message[];
	setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
	setSummaryData: React.Dispatch<React.SetStateAction<any>>;
}

const Chatbot: React.FC<ChatbotProps> = ({
	messages,
	setMessages,
	setSummaryData,
}) => {
	const [inputText, setInputText] = useState('');
	const [isLoading, setIsLoading] = useState(false);
	const messagesEndRef = useRef<HTMLDivElement>(null);

	// Initialize with welcome message if no messages
	useEffect(() => {
		if (messages.length === 0) {
			const welcomeMessage: Message = {
				id: '1',
				text: "Hello! I'm your AI lending assistant. I can help you with loan applications, generate lending memos, and provide financial analysis. How can I assist you today?",
				sender: 'agent',
				timestamp: new Date(),
			};
			setMessages([welcomeMessage]);
		}
	}, [messages.length, setMessages]);

	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
	};

	useEffect(() => {
		scrollToBottom();
	}, [messages]);

	const sendMessage = async () => {
		if (!inputText.trim() || isLoading) return;

		const userMessage: Message = {
			id: Date.now().toString(),
			text: inputText,
			sender: 'user',
			timestamp: new Date(),
		};

		setMessages((prev) => [...prev, userMessage]);
		setInputText('');
		setIsLoading(true);

		try {
			const response = await fetch('http://localhost:8000/chat', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({ message: inputText }),
			});

			if (!response.ok) {
				throw new Error('Failed to send message');
			}

			const data = await response.json();

			const agentMessage: Message = {
				id: (Date.now() + 1).toString(),
				text: data.response,
				sender: 'agent',
				timestamp: new Date(),
			};

			setMessages((prev) => [...prev, agentMessage]);

			// Update summary data when agent responds
			setSummaryData({
				lastQuery: inputText,
				lastResponse: data.response,
				timestamp: new Date(),
			});
		} catch (error) {
			console.error('Error sending message:', error);
			const errorMessage: Message = {
				id: (Date.now() + 1).toString(),
				text: 'Sorry, I encountered an error. Please try again.',
				sender: 'agent',
				timestamp: new Date(),
			};
			setMessages((prev) => [...prev, errorMessage]);
		} finally {
			setIsLoading(false);
		}
	};

	const handleKeyPress = (e: React.KeyboardEvent) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	};

	const formatTimestamp = (timestamp: Date) => {
		return timestamp.toLocaleTimeString([], {
			hour: '2-digit',
			minute: '2-digit',
		});
	};

	return (
		<div className='flex flex-col h-full'>
			{/* Chat Header */}
			<div className='bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4'>
				<div className='flex justify-between items-center'>
					<h3 className='text-lg font-semibold'>Lending Assistant</h3>
					<div className='flex items-center space-x-2'>
						<div className='w-2 h-2 bg-green-400 rounded-full animate-pulse'></div>
						<span className='text-sm'>Online</span>
					</div>
				</div>
			</div>

			{/* Messages Container */}
			<div className='flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50'>
				{messages.map((message) => (
					<div
						key={message.id}
						className={`flex ${
							message.sender === 'user' ? 'justify-end' : 'justify-start'
						}`}>
						<div
							className={`max-w-xs lg:max-w-md xl:max-w-lg ${
								message.sender === 'user'
									? 'bg-blue-600 text-white'
									: 'bg-white text-gray-800 shadow-sm border border-gray-200'
							} rounded-lg px-4 py-3`}>
							<div className='text-sm leading-relaxed whitespace-pre-wrap'>
								{message.text}
							</div>
							<div
								className={`text-xs mt-2 ${
									message.sender === 'user' ? 'text-blue-100' : 'text-gray-500'
								}`}>
								{formatTimestamp(message.timestamp)}
							</div>
						</div>
					</div>
				))}

				{isLoading && (
					<div className='flex justify-start'>
						<div className='bg-white text-gray-800 shadow-sm border border-gray-200 rounded-lg px-4 py-3'>
							<div className='flex space-x-1'>
								<div className='w-2 h-2 bg-gray-400 rounded-full animate-bounce'></div>
								<div
									className='w-2 h-2 bg-gray-400 rounded-full animate-bounce'
									style={{ animationDelay: '0.1s' }}></div>
								<div
									className='w-2 h-2 bg-gray-400 rounded-full animate-bounce'
									style={{ animationDelay: '0.2s' }}></div>
							</div>
						</div>
					</div>
				)}
				<div ref={messagesEndRef} />
			</div>

			{/* Input Container */}
			<div className='bg-white border-t border-gray-200 p-4'>
				<div className='flex space-x-3'>
					<textarea
						value={inputText}
						onChange={(e) => setInputText(e.target.value)}
						onKeyPress={handleKeyPress}
						placeholder='Ask me about lending, loan applications, or request a memo...'
						className='flex-1 resize-none border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
						rows={1}
						disabled={isLoading}
					/>
					<button
						onClick={sendMessage}
						disabled={!inputText.trim() || isLoading}
						className='bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors'>
						{isLoading ? (
							<div className='w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin'></div>
						) : (
							'Send'
						)}
					</button>
				</div>
			</div>
		</div>
	);
};

export default Chatbot;
