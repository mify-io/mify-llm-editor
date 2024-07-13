import React, {useState, useEffect, useRef} from 'react';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';
interface ChatMessage {
    id: string;
    content: string;
    isUser: boolean;
}

const Chat: React.FC = () => {
    const [messages, setMessages] = useState<ChatMessage[]>(() => {
        const savedMessages = localStorage.getItem('chatMessages');
        return savedMessages ? JSON.parse(savedMessages) : [];
    });
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({behavior: 'smooth'});
    };

    useEffect(scrollToBottom, [messages]);

    useEffect(() => {
        localStorage.setItem('chatMessages', JSON.stringify(messages));
    }, [messages]);

    const handleSend = async () => {
        if (input.trim() === '' || isLoading) return;

        const userMessage: ChatMessage = {
            id: Date.now().toString(),
            content: input,
            isUser: true,
        };
        setMessages((prevMessages) => [...prevMessages, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await axios.post('http://localhost:3001/api/chat', {message: input, project_id: 1});

            const llmMessage: ChatMessage = {
                id: (Date.now() + 1).toString(),
                content: response.data.message,
                isUser: false,
            };
            setMessages((prevMessages) => [...prevMessages, llmMessage]);
        } catch (error) {
            console.error('Error calling LLM API:', error);
            // Handle error (e.g., show an error message to the user)
        } finally {
            setIsLoading(false);
        }
    };

    const clearChat = () => {
        setMessages([]);
        localStorage.removeItem('chatMessages');
    };

    return (
        <div className="flex flex-col h-screen bg-gray-100">
            {/* Chat header */}
            <div className="bg-blue-600 text-white p-4 shadow-md">
                <h1 className="text-2xl font-bold">Mify chat</h1>
                <button
                    onClick={clearChat}
                    className="bg-red-500 text-white px-4 py-2 rounded-full hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors duration-200"
                >
                    Clear Chat
                </button>
            </div>
            {/* Chat messages area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex ${message.isUser ? 'justify-end' : 'justify-start'
                            }`}
                    >
                        <div
                            className={`max-w-xs md:max-w-md lg:max-w-lg xl:max-w-xl rounded-lg p-3 ${message.isUser
                                    ? 'bg-blue-500 text-white rounded-br-none'
                                    : 'bg-white text-gray-800 rounded-bl-none shadow-md'
                                }`}
                        >
                            {message.isUser ? (
                                <p className="text-sm">{message.content}</p>
                            ) : (
                                <ReactMarkdown className="text-sm prose prose-sm max-w-none">{message.content}</ReactMarkdown>
                            )}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-gray-200 text-gray-600 rounded-lg p-3 animate-pulse">
                            LLM is thinking...
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input area */}
            {/* Input area */}
            <div className="p-4 bg-white border-t border-gray-200">
                <div className="flex space-x-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        className="flex-1 border border-gray-300 rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Type your message..."
                        disabled={isLoading}
                    />
                    <button
                        onClick={handleSend}
                        className={`px-6 py-2 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200 ${isLoading
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-blue-500 hover:bg-blue-600 text-white'
                            }`}
                        disabled={isLoading}
                    >
                        {isLoading ? 'Sending...' : 'Send'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Chat;
