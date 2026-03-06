import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue 
} from '../components/ui/select';
import { toast } from 'sonner';
import Editor from '@monaco-editor/react';
import {
  Atom,
  MessageSquare,
  Video,
  ImageIcon,
  Globe,
  LogOut,
  Send,
  Loader2,
  Plus,
  Trash2,
  Copy,
  Download,
  Play,
  RefreshCw,
  Code2,
  History,
  ExternalLink,
  Menu,
  X,
  ChevronRight
} from 'lucide-react';
import {
  sendChatMessage,
  getConversations,
  getConversation,
  deleteConversation,
  generateVideo,
  getVideoStatus,
  generateImage,
  cloneSite,
  BACKEND_URL
} from '../lib/api';

// Mobile Bottom Nav
const MobileNav = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'chat', icon: MessageSquare, label: 'Chat' },
    { id: 'video', icon: Video, label: 'Video' },
    { id: 'image', icon: ImageIcon, label: 'Image' },
    { id: 'clone', icon: Globe, label: 'Clone' },
    { id: 'history', icon: History, label: 'History' },
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 h-16 bg-card border-t border-white/10 flex items-center justify-around px-2 md:hidden z-50">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          className={`flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-lg transition-colors ${
            activeTab === tab.id 
              ? 'text-blue-400 bg-blue-500/10' 
              : 'text-muted-foreground'
          }`}
          data-testid={`mobile-${tab.id}-btn`}
        >
          <tab.icon className="w-5 h-5" strokeWidth={1.5} />
          <span className="text-[10px] font-medium">{tab.label}</span>
        </button>
      ))}
    </div>
  );
};

// Desktop Sidebar Component
const Sidebar = ({ activeTab, setActiveTab }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const tabs = [
    { id: 'chat', icon: MessageSquare, label: 'AI Chat' },
    { id: 'video', icon: Video, label: 'Video' },
    { id: 'image', icon: ImageIcon, label: 'Image' },
    { id: 'clone', icon: Globe, label: 'Clone' },
    { id: 'history', icon: History, label: 'History' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="hidden md:flex w-16 bg-card border-r border-white/10 flex-col h-screen">
      {/* Logo */}
      <div className="h-16 flex items-center justify-center border-b border-white/10">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
          <Atom className="w-5 h-5 text-white" strokeWidth={2} />
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 py-4 flex flex-col items-center gap-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`sidebar-icon w-11 h-11 flex items-center justify-center rounded-xl ${
              activeTab === tab.id ? 'active' : ''
            }`}
            title={tab.label}
            data-testid={`sidebar-${tab.id}-btn`}
          >
            <tab.icon className="w-5 h-5" strokeWidth={1.5} />
          </button>
        ))}
      </div>

      {/* Logout */}
      <div className="py-4 flex flex-col items-center border-t border-white/10">
        <button
          onClick={handleLogout}
          className="sidebar-icon w-11 h-11 flex items-center justify-center rounded-xl text-muted-foreground hover:text-red-400"
          title="Logout"
          data-testid="sidebar-logout-btn"
        >
          <LogOut className="w-5 h-5" strokeWidth={1.5} />
        </button>
      </div>
    </div>
  );
};

// Chat Panel Component
const ChatPanel = ({ conversationId, setConversationId, onRefresh }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [codeContext, setCodeContext] = useState('');
  const [showContext, setShowContext] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (conversationId) {
      loadConversation(conversationId);
    } else {
      setMessages([]);
    }
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversation = async (id) => {
    try {
      const conv = await getConversation(id);
      setMessages(conv.messages || []);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage, timestamp: new Date().toISOString() }]);
    setLoading(true);

    try {
      const response = await sendChatMessage(userMessage, conversationId, codeContext || null);
      setConversationId(response.conversation_id);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.response, 
        timestamp: new Date().toISOString() 
      }]);
      onRefresh();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send message');
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setConversationId(null);
    setMessages([]);
    setCodeContext('');
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied!');
  };

  const renderMessage = (msg, idx) => {
    const isUser = msg.role === 'user';
    
    const renderContent = (content) => {
      const parts = content.split(/(```[\s\S]*?```)/g);
      return parts.map((part, i) => {
        if (part.startsWith('```')) {
          const match = part.match(/```(\w+)?\n?([\s\S]*?)```/);
          const lang = match?.[1] || '';
          const code = match?.[2] || part.slice(3, -3);
          return (
            <div key={i} className="code-block my-3 relative group">
              <div className="flex items-center justify-between px-3 py-2 bg-white/5 border-b border-white/10 text-xs">
                <span className="text-muted-foreground font-mono">{lang || 'code'}</span>
                <button 
                  onClick={() => copyToClipboard(code)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground"
                >
                  <Copy className="w-3.5 h-3.5" />
                </button>
              </div>
              <pre className="p-4 overflow-x-auto text-sm font-mono">
                <code>{code}</code>
              </pre>
            </div>
          );
        }
        return <span key={i} className="whitespace-pre-wrap">{part}</span>;
      });
    };

    return (
      <motion.div
        key={idx}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`p-4 ${isUser ? 'chat-message-user' : 'chat-message-assistant'} mx-2 md:mx-4 mb-3`}
      >
        <div className="flex items-start gap-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
            isUser 
              ? 'bg-gradient-to-br from-blue-500 to-purple-600' 
              : 'bg-white/10'
          }`}>
            {isUser ? (
              <span className="text-xs font-bold text-white">U</span>
            ) : (
              <Atom className="w-4 h-4 text-blue-400" strokeWidth={2} />
            )}
          </div>
          <div className="flex-1 min-w-0 overflow-hidden">
            <div className="text-xs text-muted-foreground mb-1">
              {isUser ? 'You' : 'ATOM AI'}
            </div>
            <div className={`text-sm leading-relaxed ${!isUser ? 'font-mono' : ''}`}>
              {renderContent(msg.content)}
            </div>
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-14 px-4 flex items-center justify-between border-b border-white/10 shrink-0">
        <div className="flex items-center gap-2">
          <Code2 className="w-5 h-5 text-blue-400" strokeWidth={1.5} />
          <span className="font-semibold">AI Assistant</span>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={handleNewChat}
          className="text-muted-foreground hover:text-foreground h-8"
          data-testid="new-chat-btn"
        >
          <Plus className="w-4 h-4 mr-1" />
          New
        </Button>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1">
        <div className="py-4">
          {messages.length === 0 ? (
            <div className="text-center py-16 px-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mx-auto mb-4">
                <Atom className="w-8 h-8 text-blue-400" strokeWidth={1.5} />
              </div>
              <h3 className="text-lg font-semibold mb-2">How can I help?</h3>
              <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                Ask me to write code, debug issues, explain concepts, or help with any programming task.
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => renderMessage(msg, idx))
          )}
          {loading && (
            <div className="p-4 chat-message-assistant mx-2 md:mx-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
                  <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                </div>
                <span className="text-sm text-muted-foreground">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Context Toggle */}
      {showContext && (
        <div className="px-4 py-3 border-t border-white/10 bg-secondary/30">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground">Code Context</span>
            <button 
              onClick={() => setShowContext(false)}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <Textarea
            value={codeContext}
            onChange={(e) => setCodeContext(e.target.value)}
            placeholder="Paste code for context..."
            className="h-20 text-xs font-mono bg-secondary/50 border-white/10 resize-none rounded-lg"
          />
        </div>
      )}

      {/* Input */}
      <div className="p-3 md:p-4 border-t border-white/10 shrink-0 pb-20 md:pb-4">
        <div className="flex items-center gap-2 mb-2">
          <button
            onClick={() => setShowContext(!showContext)}
            className={`text-xs flex items-center gap-1 ${showContext ? 'text-blue-400' : 'text-muted-foreground'} hover:text-blue-400 transition-colors`}
          >
            <ChevronRight className={`w-3 h-3 transition-transform ${showContext ? 'rotate-90' : ''}`} />
            Add Code Context
          </button>
        </div>
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask anything about code..."
            className="flex-1 h-11 bg-secondary/50 border-white/10 rounded-lg text-sm"
            data-testid="chat-input"
          />
          <Button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="h-11 w-11 btn-gradient rounded-lg"
            data-testid="chat-send-btn"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

// Video Generation Panel
const VideoPanel = () => {
  const [prompt, setPrompt] = useState('');
  const [size, setSize] = useState('1280x720');
  const [duration, setDuration] = useState('4');
  const [loading, setLoading] = useState(false);
  const [videoId, setVideoId] = useState(null);
  const [status, setStatus] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt');
      return;
    }

    setLoading(true);
    setVideoUrl(null);
    setStatus('processing');

    try {
      const response = await generateVideo(prompt, size, parseInt(duration));
      setVideoId(response.video_id);
      pollStatus(response.video_id);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start video generation');
      setLoading(false);
      setStatus(null);
    }
  };

  const pollStatus = async (id) => {
    const interval = setInterval(async () => {
      try {
        const response = await getVideoStatus(id);
        setStatus(response.status);

        if (response.status === 'completed') {
          clearInterval(interval);
          setVideoUrl(`${BACKEND_URL}${response.video_url}`);
          setLoading(false);
          toast.success('Video generated!');
        } else if (response.status === 'failed') {
          clearInterval(interval);
          setLoading(false);
          toast.error('Video generation failed');
        }
      } catch (error) {
        console.error('Status poll error:', error);
      }
    }, 5000);

    setTimeout(() => clearInterval(interval), 900000);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 px-4 flex items-center border-b border-white/10 shrink-0">
        <Video className="w-5 h-5 text-blue-400 mr-2" strokeWidth={1.5} />
        <span className="font-semibold">Video Generation</span>
        <span className="ml-2 text-xs text-muted-foreground">(Sora 2)</span>
      </div>

      <div className="flex-1 p-4 md:p-6 overflow-auto pb-20 md:pb-6">
        <div className="max-w-xl mx-auto">
          <div className="space-y-2 mb-5">
            <label className="text-sm font-medium">Describe your video</label>
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="A futuristic city at sunset with flying cars..."
              className="h-28 bg-secondary/50 border-white/10 resize-none rounded-lg"
              data-testid="video-prompt-input"
            />
          </div>

          <div className="grid grid-cols-2 gap-3 mb-5">
            <div className="space-y-2">
              <label className="text-sm font-medium">Resolution</label>
              <Select value={size} onValueChange={setSize}>
                <SelectTrigger className="bg-secondary/50 border-white/10 rounded-lg h-11" data-testid="video-size-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1280x720">HD (1280x720)</SelectItem>
                  <SelectItem value="1792x1024">Wide (1792x1024)</SelectItem>
                  <SelectItem value="1024x1792">Portrait</SelectItem>
                  <SelectItem value="1024x1024">Square</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Duration</label>
              <Select value={duration} onValueChange={setDuration}>
                <SelectTrigger className="bg-secondary/50 border-white/10 rounded-lg h-11" data-testid="video-duration-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="4">4 seconds</SelectItem>
                  <SelectItem value="8">8 seconds</SelectItem>
                  <SelectItem value="12">12 seconds</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            onClick={handleGenerate}
            disabled={loading || !prompt.trim()}
            className="w-full h-12 btn-gradient font-semibold rounded-lg"
            data-testid="video-generate-btn"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Generate Video
              </>
            )}
          </Button>

          {status && (
            <div className="mt-5 p-4 bg-secondary/30 border border-white/10 rounded-xl">
              <div className="flex items-center gap-2 mb-2">
                <div className={`status-dot ${status}`} />
                <span className="text-sm font-medium capitalize">{status}</span>
              </div>
              {status === 'processing' && (
                <p className="text-xs text-muted-foreground">
                  This may take 2-10 minutes depending on duration.
                </p>
              )}
            </div>
          )}

          {videoUrl && (
            <div className="mt-5 video-container rounded-xl">
              <video src={videoUrl} controls className="w-full rounded-t-xl" data-testid="video-preview" />
              <div className="p-3 border-t border-white/10 flex justify-end">
                <a href={videoUrl} download className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
                  <Download className="w-3 h-3" />
                  Download
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Image Generation Panel
const ImagePanel = () => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [imageData, setImageData] = useState(null);
  const [textResponse, setTextResponse] = useState('');

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt');
      return;
    }

    setLoading(true);
    setImageData(null);

    try {
      const response = await generateImage(prompt);
      setImageData(response.image_data);
      setTextResponse(response.text_response || '');
      toast.success('Image generated!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate image');
    } finally {
      setLoading(false);
    }
  };

  const downloadImage = () => {
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${imageData}`;
    link.download = 'atom-image.png';
    link.click();
  };

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 px-4 flex items-center border-b border-white/10 shrink-0">
        <ImageIcon className="w-5 h-5 text-blue-400 mr-2" strokeWidth={1.5} />
        <span className="font-semibold">Image Generation</span>
        <span className="ml-2 text-xs text-muted-foreground">(Nano Banana)</span>
      </div>

      <div className="flex-1 p-4 md:p-6 overflow-auto pb-20 md:pb-6">
        <div className="max-w-xl mx-auto">
          <div className="space-y-2 mb-5">
            <label className="text-sm font-medium">Describe your image</label>
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="A cyberpunk cat wearing neon goggles..."
              className="h-28 bg-secondary/50 border-white/10 resize-none rounded-lg"
              data-testid="image-prompt-input"
            />
          </div>

          <Button
            onClick={handleGenerate}
            disabled={loading || !prompt.trim()}
            className="w-full h-12 btn-gradient font-semibold rounded-lg"
            data-testid="image-generate-btn"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <ImageIcon className="w-4 h-4 mr-2" />
                Generate Image
              </>
            )}
          </Button>

          {imageData && (
            <div className="mt-5 image-preview rounded-xl">
              <img 
                src={`data:image/png;base64,${imageData}`} 
                alt="Generated" 
                className="w-full rounded-t-xl"
                data-testid="image-preview"
              />
              <div className="p-3 border-t border-white/10 flex justify-between items-center">
                {textResponse && (
                  <p className="text-xs text-muted-foreground truncate max-w-[70%]">{textResponse}</p>
                )}
                <button onClick={downloadImage} className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
                  <Download className="w-3 h-3" />
                  Download
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Site Clone Panel
const ClonePanel = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleClone = async () => {
    if (!url.trim()) {
      toast.error('Please enter a URL');
      return;
    }

    try {
      new URL(url);
    } catch {
      toast.error('Please enter a valid URL');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await cloneSite(url);
      setResult(response);
      toast.success('Site cloned!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to clone site');
    } finally {
      setLoading(false);
    }
  };

  const copyCode = () => {
    navigator.clipboard.writeText(result.code);
    toast.success('Code copied!');
  };

  const downloadCode = () => {
    const blob = new Blob([result.code], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'cloned-site.html';
    link.click();
  };

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 px-4 flex items-center border-b border-white/10 shrink-0">
        <Globe className="w-5 h-5 text-blue-400 mr-2" strokeWidth={1.5} />
        <span className="font-semibold">Website Cloner</span>
      </div>

      <div className="flex-1 p-4 md:p-6 overflow-auto pb-20 md:pb-6">
        <div className="max-w-3xl mx-auto">
          <div className="space-y-2 mb-5">
            <label className="text-sm font-medium">Website URL</label>
            <div className="flex gap-2">
              <Input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com"
                className="flex-1 h-11 bg-secondary/50 border-white/10 rounded-lg font-mono text-sm"
                data-testid="clone-url-input"
              />
              <Button
                onClick={handleClone}
                disabled={loading || !url.trim()}
                className="h-11 px-6 btn-gradient font-semibold rounded-lg"
                data-testid="clone-submit-btn"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Clone'}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Enter any URL to generate responsive HTML/CSS code
            </p>
          </div>

          {result && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <Button variant="outline" size="sm" onClick={copyCode} className="text-xs border-white/10 rounded-lg">
                  <Copy className="w-3 h-3 mr-1" /> Copy
                </Button>
                <Button variant="outline" size="sm" onClick={downloadCode} className="text-xs border-white/10 rounded-lg">
                  <Download className="w-3 h-3 mr-1" /> Download
                </Button>
                <a
                  href={`${BACKEND_URL}${result.preview_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                >
                  <ExternalLink className="w-3 h-3" /> Preview
                </a>
              </div>

              <div className="monaco-container h-[400px] md:h-[500px] rounded-xl">
                <Editor
                  height="100%"
                  defaultLanguage="html"
                  value={result.code}
                  theme="vs-dark"
                  options={{
                    readOnly: true,
                    minimap: { enabled: false },
                    fontSize: 13,
                    fontFamily: "'JetBrains Mono', monospace",
                    scrollBeyondLastLine: false,
                    wordWrap: 'on'
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// History Panel
const HistoryPanel = ({ conversations, onSelect, onDelete, onRefresh }) => {
  return (
    <div className="flex flex-col h-full">
      <div className="h-14 px-4 flex items-center justify-between border-b border-white/10 shrink-0">
        <div className="flex items-center">
          <History className="w-5 h-5 text-blue-400 mr-2" strokeWidth={1.5} />
          <span className="font-semibold">History</span>
        </div>
        <Button size="sm" variant="ghost" onClick={onRefresh} className="h-8 w-8 p-0">
          <RefreshCw className="w-4 h-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1 pb-20 md:pb-0">
        <div className="p-4 space-y-2">
          {conversations.length === 0 ? (
            <div className="text-center py-12">
              <MessageSquare className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">No conversations yet</p>
            </div>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className="p-3 bg-secondary/30 border border-white/5 hover:border-blue-500/30 rounded-xl transition-colors group cursor-pointer"
                onClick={() => onSelect(conv.id)}
                data-testid={`history-item-${conv.id}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium truncate">{conv.title}</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      {conv.messages?.length || 0} messages
                    </p>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-muted-foreground hover:text-red-400 transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

// Main Workspace Component
export default function WorkspacePage() {
  const { user, loading: authLoading, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('chat');
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);

  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/login');
    }
  }, [user, authLoading, navigate]);

  useEffect(() => {
    if (user) {
      loadConversations();
    }
  }, [user]);

  const loadConversations = async () => {
    try {
      const convs = await getConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const handleSelectConversation = (id) => {
    setConversationId(id);
    setActiveTab('chat');
  };

  const handleDeleteConversation = async (id) => {
    try {
      await deleteConversation(id);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (conversationId === id) {
        setConversationId(null);
      }
      toast.success('Deleted');
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="bg-background min-h-screen md:grid md:grid-cols-[64px_1fr]" data-testid="workspace-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <MobileNav activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <div className="flex-1 h-screen overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="h-full"
          >
            {activeTab === 'chat' && (
              <ChatPanel
                conversationId={conversationId}
                setConversationId={setConversationId}
                onRefresh={loadConversations}
              />
            )}
            {activeTab === 'video' && <VideoPanel />}
            {activeTab === 'image' && <ImagePanel />}
            {activeTab === 'clone' && <ClonePanel />}
            {activeTab === 'history' && (
              <HistoryPanel
                conversations={conversations}
                onSelect={handleSelectConversation}
                onDelete={handleDeleteConversation}
                onRefresh={loadConversations}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
