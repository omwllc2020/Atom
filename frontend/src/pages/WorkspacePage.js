import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { ScrollArea } from '../components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
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
  Zap,
  MessageSquare,
  Video,
  ImageIcon,
  Globe,
  Settings,
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
  ChevronLeft,
  ChevronRight,
  ExternalLink
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

// Sidebar Component
const Sidebar = ({ activeTab, setActiveTab, onNewChat }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const tabs = [
    { id: 'chat', icon: MessageSquare, label: 'AI Chat' },
    { id: 'video', icon: Video, label: 'Video Gen' },
    { id: 'image', icon: ImageIcon, label: 'Image Gen' },
    { id: 'clone', icon: Globe, label: 'Site Clone' },
    { id: 'history', icon: History, label: 'History' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="w-[60px] bg-card border-r border-border flex flex-col h-screen">
      {/* Logo */}
      <div className="h-14 flex items-center justify-center border-b border-border">
        <Zap className="w-6 h-6 text-primary" strokeWidth={1.5} />
      </div>

      {/* Navigation */}
      <div className="flex-1 py-4 flex flex-col items-center gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`sidebar-icon w-10 h-10 flex items-center justify-center rounded-sm ${
              activeTab === tab.id ? 'active' : ''
            }`}
            title={tab.label}
            data-testid={`sidebar-${tab.id}-btn`}
          >
            <tab.icon className="w-5 h-5" strokeWidth={1.5} />
          </button>
        ))}
      </div>

      {/* Bottom Actions */}
      <div className="py-4 flex flex-col items-center gap-2 border-t border-border">
        <button
          onClick={handleLogout}
          className="sidebar-icon w-10 h-10 flex items-center justify-center rounded-sm text-muted-foreground hover:text-destructive"
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
const ChatPanel = ({ conversationId, setConversationId, conversations, setConversations, onRefresh }) => {
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
    toast.success('Copied to clipboard');
  };

  const renderMessage = (msg, idx) => {
    const isUser = msg.role === 'user';
    
    // Simple markdown-like rendering for code blocks
    const renderContent = (content) => {
      const parts = content.split(/(```[\s\S]*?```)/g);
      return parts.map((part, i) => {
        if (part.startsWith('```')) {
          const match = part.match(/```(\w+)?\n?([\s\S]*?)```/);
          const lang = match?.[1] || '';
          const code = match?.[2] || part.slice(3, -3);
          return (
            <div key={i} className="code-block my-3 relative group">
              <div className="flex items-center justify-between px-3 py-2 bg-muted/50 border-b border-border text-xs">
                <span className="text-muted-foreground font-mono">{lang || 'code'}</span>
                <button 
                  onClick={() => copyToClipboard(code)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Copy className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
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
        className={`p-4 ${isUser ? 'chat-message-user' : 'chat-message-assistant'}`}
      >
        <div className="flex items-start gap-3">
          <div className={`w-8 h-8 flex items-center justify-center shrink-0 ${
            isUser ? 'bg-primary/20' : 'bg-muted'
          }`}>
            {isUser ? (
              <span className="text-xs font-bold text-primary">U</span>
            ) : (
              <Zap className="w-4 h-4 text-primary" strokeWidth={1.5} />
            )}
          </div>
          <div className="flex-1 overflow-hidden">
            <div className="text-xs text-muted-foreground mb-1 font-mono">
              {isUser ? 'You' : 'Forge AI'}
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
      <div className="h-14 px-4 flex items-center justify-between border-b border-border shrink-0">
        <div className="flex items-center gap-2">
          <Code2 className="w-5 h-5 text-primary" strokeWidth={1.5} />
          <span className="font-semibold font-[Outfit]">AI Code Assistant</span>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={handleNewChat}
          className="text-muted-foreground hover:text-foreground"
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
            <div className="text-center py-20 px-4">
              <Zap className="w-12 h-12 text-primary/30 mx-auto mb-4" strokeWidth={1} />
              <h3 className="text-lg font-semibold font-[Outfit] mb-2">Start a conversation</h3>
              <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                Ask me to write code, debug issues, explain concepts, or help with any programming task.
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => renderMessage(msg, idx))
          )}
          {loading && (
            <div className="p-4 chat-message-assistant">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-muted flex items-center justify-center">
                  <Loader2 className="w-4 h-4 text-primary animate-spin" />
                </div>
                <span className="text-sm text-muted-foreground font-mono">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Context Toggle */}
      {showContext && (
        <div className="px-4 py-3 border-t border-border bg-muted/30">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground font-mono">Code Context</span>
            <button 
              onClick={() => setShowContext(false)}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Hide
            </button>
          </div>
          <Textarea
            value={codeContext}
            onChange={(e) => setCodeContext(e.target.value)}
            placeholder="Paste code for context..."
            className="h-24 text-xs font-mono bg-input border-border resize-none"
          />
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-border shrink-0">
        <div className="flex items-center gap-2 mb-2">
          <button
            onClick={() => setShowContext(!showContext)}
            className={`text-xs ${showContext ? 'text-primary' : 'text-muted-foreground'} hover:text-primary transition-colors`}
          >
            + Add Code Context
          </button>
        </div>
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask anything about code..."
            className="flex-1 h-12 bg-input border-border font-mono text-sm"
            data-testid="chat-input"
          />
          <Button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="h-12 w-12 bg-primary text-primary-foreground hover:bg-primary/90 neon-glow-hover btn-press"
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
          toast.success('Video generated successfully!');
        } else if (response.status === 'failed') {
          clearInterval(interval);
          setLoading(false);
          toast.error('Video generation failed');
        }
      } catch (error) {
        console.error('Status poll error:', error);
      }
    }, 5000);

    // Stop polling after 15 minutes
    setTimeout(() => clearInterval(interval), 900000);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-14 px-4 flex items-center border-b border-border shrink-0">
        <Video className="w-5 h-5 text-primary mr-2" strokeWidth={1.5} />
        <span className="font-semibold font-[Outfit]">Text to Video</span>
        <span className="ml-2 text-xs text-muted-foreground">(Sora 2)</span>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 overflow-auto">
        <div className="max-w-2xl">
          {/* Prompt */}
          <div className="space-y-2 mb-6">
            <label className="text-sm font-medium">Describe your video</label>
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="A futuristic city at sunset with flying cars..."
              className="h-32 bg-input border-border resize-none"
              data-testid="video-prompt-input"
            />
          </div>

          {/* Options */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="space-y-2">
              <label className="text-sm font-medium">Resolution</label>
              <Select value={size} onValueChange={setSize}>
                <SelectTrigger className="bg-input border-border" data-testid="video-size-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1280x720">1280x720 (HD)</SelectItem>
                  <SelectItem value="1792x1024">1792x1024 (Widescreen)</SelectItem>
                  <SelectItem value="1024x1792">1024x1792 (Portrait)</SelectItem>
                  <SelectItem value="1024x1024">1024x1024 (Square)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Duration</label>
              <Select value={duration} onValueChange={setDuration}>
                <SelectTrigger className="bg-input border-border" data-testid="video-duration-select">
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

          {/* Generate Button */}
          <Button
            onClick={handleGenerate}
            disabled={loading || !prompt.trim()}
            className="w-full h-12 bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider text-xs neon-glow-hover btn-press"
            data-testid="video-generate-btn"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating... (this may take a few minutes)
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Generate Video
              </>
            )}
          </Button>

          {/* Status */}
          {status && (
            <div className="mt-6 p-4 bg-card border border-border rounded-sm">
              <div className="flex items-center gap-2 mb-2">
                <div className={`status-dot ${status}`} />
                <span className="text-sm font-mono capitalize">{status}</span>
              </div>
              {status === 'processing' && (
                <p className="text-xs text-muted-foreground">
                  Video generation can take 2-10 minutes depending on duration and complexity.
                </p>
              )}
            </div>
          )}

          {/* Video Preview */}
          {videoUrl && (
            <div className="mt-6 video-container">
              <video 
                src={videoUrl} 
                controls 
                className="w-full"
                data-testid="video-preview"
              >
                Your browser does not support video playback.
              </video>
              <div className="p-3 border-t border-border flex justify-end">
                <a 
                  href={videoUrl} 
                  download 
                  className="text-xs text-primary hover:underline flex items-center gap-1"
                >
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
      toast.success('Image generated successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate image');
    } finally {
      setLoading(false);
    }
  };

  const downloadImage = () => {
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${imageData}`;
    link.download = 'forge-image.png';
    link.click();
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-14 px-4 flex items-center border-b border-border shrink-0">
        <ImageIcon className="w-5 h-5 text-primary mr-2" strokeWidth={1.5} />
        <span className="font-semibold font-[Outfit]">Image Generation</span>
        <span className="ml-2 text-xs text-muted-foreground">(Nano Banana)</span>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 overflow-auto">
        <div className="max-w-2xl">
          {/* Prompt */}
          <div className="space-y-2 mb-6">
            <label className="text-sm font-medium">Describe your image</label>
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="A cyberpunk cat wearing neon goggles in a rainy alley..."
              className="h-32 bg-input border-border resize-none"
              data-testid="image-prompt-input"
            />
          </div>

          {/* Generate Button */}
          <Button
            onClick={handleGenerate}
            disabled={loading || !prompt.trim()}
            className="w-full h-12 bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider text-xs neon-glow-hover btn-press"
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

          {/* Image Preview */}
          {imageData && (
            <div className="mt-6 image-preview">
              <img 
                src={`data:image/png;base64,${imageData}`} 
                alt="Generated" 
                className="w-full"
                data-testid="image-preview"
              />
              <div className="p-3 border-t border-border flex justify-between items-center">
                {textResponse && (
                  <p className="text-xs text-muted-foreground truncate max-w-[70%]">{textResponse}</p>
                )}
                <button 
                  onClick={downloadImage}
                  className="text-xs text-primary hover:underline flex items-center gap-1"
                >
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

    // Basic URL validation
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
      toast.success('Site cloned successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to clone site');
    } finally {
      setLoading(false);
    }
  };

  const copyCode = () => {
    navigator.clipboard.writeText(result.code);
    toast.success('Code copied to clipboard');
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
      {/* Header */}
      <div className="h-14 px-4 flex items-center border-b border-border shrink-0">
        <Globe className="w-5 h-5 text-primary mr-2" strokeWidth={1.5} />
        <span className="font-semibold font-[Outfit]">Site Cloner</span>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 overflow-auto">
        <div className="max-w-4xl">
          {/* URL Input */}
          <div className="space-y-2 mb-6">
            <label className="text-sm font-medium">Website URL to clone</label>
            <div className="flex gap-2">
              <Input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com"
                className="flex-1 h-12 bg-input border-border font-mono"
                data-testid="clone-url-input"
              />
              <Button
                onClick={handleClone}
                disabled={loading || !url.trim()}
                className="h-12 px-6 bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider text-xs neon-glow-hover btn-press"
                data-testid="clone-submit-btn"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  'Clone'
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Enter any website URL and we'll generate responsive HTML/CSS code to recreate it.
            </p>
          </div>

          {/* Result */}
          {result && (
            <div className="space-y-4">
              {/* Actions */}
              <div className="flex items-center gap-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyCode}
                  className="text-xs"
                >
                  <Copy className="w-3 h-3 mr-1" />
                  Copy Code
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={downloadCode}
                  className="text-xs"
                >
                  <Download className="w-3 h-3 mr-1" />
                  Download
                </Button>
                <a
                  href={`${BACKEND_URL}${result.preview_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline flex items-center gap-1"
                >
                  <ExternalLink className="w-3 h-3" />
                  Preview
                </a>
              </div>

              {/* Code Editor */}
              <div className="monaco-container h-[500px]">
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
      {/* Header */}
      <div className="h-14 px-4 flex items-center justify-between border-b border-border shrink-0">
        <div className="flex items-center">
          <History className="w-5 h-5 text-primary mr-2" strokeWidth={1.5} />
          <span className="font-semibold font-[Outfit]">Conversation History</span>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={onRefresh}
          className="text-muted-foreground hover:text-foreground"
        >
          <RefreshCw className="w-4 h-4" />
        </Button>
      </div>

      {/* List */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-2">
          {conversations.length === 0 ? (
            <div className="text-center py-10">
              <MessageSquare className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">No conversations yet</p>
            </div>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className="p-3 bg-card border border-border/50 hover:border-primary/30 transition-colors group cursor-pointer"
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
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(conv.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-muted-foreground hover:text-destructive transition-all"
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
  const { user, loading: authLoading } = useAuth();
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
      toast.success('Conversation deleted');
    } catch (error) {
      toast.error('Failed to delete conversation');
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="workspace-container bg-background" data-testid="workspace-container">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab}
        onNewChat={() => setConversationId(null)}
      />
      
      <div className="flex-1 flex overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
            className="flex-1"
          >
            {activeTab === 'chat' && (
              <ChatPanel
                conversationId={conversationId}
                setConversationId={setConversationId}
                conversations={conversations}
                setConversations={setConversations}
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
