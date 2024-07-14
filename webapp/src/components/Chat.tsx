import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';

interface ChatMessage {
    id: string;
    content: string;
    isUser: boolean;
}

interface ChatProject {
    id: string;
    name: string;
}

const ChatList: React.FC<{
    projects: ChatProject[];
    activeProject: string;
    onSelectProject: (id: string) => void;
    onNewProject: () => void;
}> = ({ projects, activeProject, onSelectProject, onNewProject }) => {
    return (
        <div className="w-64 bg-chat-frame text-gray-300 p-4 overflow-y-auto">
            <button
                onClick={onNewProject}
                className="w-full bg-new-button-100 text-white px-4 py-2 rounded-md mb-4 hover:bg-new-button-200 transition-colors duration-200"
            >
                New Project
            </button>
            <ul>
                {projects.map((project) => (
                    <li
                        key={project.id}
                        className={`cursor-pointer p-2 rounded-md mb-2 ${
                            activeProject === project.id ? 'bg-active-project text-white' : 'hover:bg-gray-800'
                        }`}
                        onClick={() => onSelectProject(project.id)}
                    >
                        {project.name}
                    </li>
                ))}
            </ul>
        </div>
    );
};

const NewProjectModal: React.FC<{
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (name: string) => void;
}> = ({ isOpen, onClose, onSubmit }) => {
    const [projectName, setProjectName] = useState('');

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg shadow-lg">
                <h2 className="text-xl font-bold mb-4 text-gray-800">Create New Project</h2>
                <input
                    type="text"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="Enter project name"
                    className="w-full p-2 border border-gray-300 rounded mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <div className="flex justify-end space-x-2">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors duration-200"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={() => {
                            if (projectName.trim()) {
                                onSubmit(projectName);
                                setProjectName('');
                            }
                        }}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors duration-200"
                    >
                        Create
                    </button>
                </div>
            </div>
        </div>
    );
};

const Chat: React.FC = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [projects, setProjects] = useState<ChatProject[]>([]);
    const [activeProject, setActiveProject] = useState<string>('');
    const [isNewProjectModalOpen, setIsNewProjectModalOpen] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const fetchChatProjects = async () => {
        try {
            const response = await axios.get('http://localhost:3001/api/chat/projects');
            setProjects(response.data);
            if (response.data.length > 0) {
                setActiveProject(response.data[0].id);
            }
        } catch (error) {
            console.error('Error fetching chat projects:', error);
        }
    };

    useEffect(scrollToBottom, [messages]);

    useEffect(() => {
        fetchChatProjects();
    }, []);

    useEffect(() => {
        const fetchChatHistory = async () => {
            if (!activeProject) return;
            try {
                const response = await axios.get(`http://localhost:3001/api/chat/history?project_id=${activeProject}`);
                setMessages(response.data);
            } catch (error) {
                console.error('Error fetching chat history:', error);
            }
        };

        fetchChatHistory();
    }, [activeProject]);

    const handleSend = async () => {
        if (input.trim() === '' || isLoading || !activeProject) return;

        const userMessage: ChatMessage = {
            id: Date.now().toString(),
            content: input,
            isUser: true,
        };
        setMessages((prevMessages) => [...prevMessages, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await axios.post('http://localhost:3001/api/chat', { message: input, project_id: activeProject });

            const llmMessage: ChatMessage = {
                id: (Date.now() + 1).toString(),
                content: response.data.message,
                isUser: false,
            };
            setMessages((prevMessages) => [...prevMessages, llmMessage]);
        } catch (error) {
            console.error('Error calling LLM API:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const clearChat = async () => {
        if (!activeProject) return;
        try {
            await axios.delete(`http://localhost:3001/api/chat/history?project_id=${activeProject}`);
            setMessages([]);
            fetchChatProjects();
        } catch (error) {
            console.error('Error clearing chat history:', error);
        }
    };

    const handleNewProject = async (projectName: string) => {
        try {
            const response = await axios.post('http://localhost:3001/api/chat/projects', { name: projectName });
            setProjects((prevProjects) => [...prevProjects, response.data]);
            setActiveProject(response.data.id);
            setIsNewProjectModalOpen(false);
        } catch (error) {
            console.error('Error creating new project:', error);
        }
    };

    return (
        <div className="flex h-screen bg-gray-100">
            <ChatList
                projects={projects}
                activeProject={activeProject}
                onSelectProject={setActiveProject}
                onNewProject={() => setIsNewProjectModalOpen(true)}
            />
            <div className="flex flex-col flex-grow">
                {/* Chat header */}
                <div className="bg-chat-frame text-white p-4 shadow-md flex justify-between items-center">
                    <h1 className="text-2xl font-bold">Mify LLM Agent</h1>
                    <button
                        onClick={clearChat}
                        className="bg-delete-button-100 text-gray-200 px-4 py-2 rounded-md hover:bg-delete-button-200 focus:outline-none transition-colors duration-200"
                    >
                        Delete Project
                    </button>
                </div>
                {/* Chat messages area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-chat-background">
                    {messages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex ${
                                message.isUser ? 'justify-end' : 'justify-start'
                            }`}
                        >
                            <div
                                className={`max-w-xs md:max-w-md lg:max-w-lg xl:max-w-xl rounded-lg p-3 ${
                                    message.isUser
                                        ? 'bg-user-message text-white rounded-br-none'
                                        : 'bg-llm-message text-gray-300 rounded-bl-none shadow-md'
                                }`}
                            >
                                {message.isUser ? (
                                    <p className="text-sm">{message.content}</p>
                                ) : (
                                    <ReactMarkdown className="text-sm prose prose-sm max-w-none">
                                        {message.content}
                                    </ReactMarkdown>
                                )}
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="bg-llm-message text-gray-600 rounded-lg p-3 animate-pulse shadow-md">
                                LLM is thinking...
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input area */}
                <div className="p-4 bg-chat-frame">
                    <div className="flex space-x-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                            className="flex-1 text-gray-200 bg-gray-800 rounded-full px-4 py-2 focus:outline-none focus:border-transparent"
                            placeholder="Type your message..."
                            disabled={isLoading || !activeProject}
                        />
                        <button
                            onClick={handleSend}
                            className={`px-6 py-2 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200 text-gray-300 ${
                                isLoading || !activeProject
                                    ? 'bg-gray-400 cursor-not-allowed'
                                    : 'bg-send-button-100 hover:bg-send-button-200 text-white'
                            }`}
                            disabled={isLoading || !activeProject}
                        >
                            {isLoading ? 'Sending...' : 'Send'}
                        </button>
                    </div>
                </div>
            </div>
            <NewProjectModal
                isOpen={isNewProjectModalOpen}
                onClose={() => setIsNewProjectModalOpen(false)}
                onSubmit={handleNewProject}
            />
        </div>
    );
}

export default Chat;
