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
  X,
  ChevronRight,
  FolderOpen,
  File,
  FileCode,
  Terminal,
  Wand2,
  Check,
  AlertCircle,
  Eye,
  Settings,
  Zap,
  Upload,
  Image as ImageLucide,
  Film
} from 'lucide-react';
import {
  sendChatMessage,
  getConversations,
  getConversation,
  deleteConversation,
  generateVideo,
  generateVideoFromMedia,
  getVideoStatus,
  generateImage,
  cloneSite,
  executeCode,
  autoFixCode,
  autoFixLoop,
  createProject,
  getProjects,
  getProject,
  deleteProject,
  addFileToProject,
  updateFile,
  deleteFile,
  BACKEND_URL
} from '../lib/api';

// File icon helper
const getFileIcon = (filename) => {
  const ext = filename.split('.').pop().toLowerCase();
  const iconMap = {
    'py': '🐍',
    'js': '📜',
    'ts': '📘',
    'html': '🌐',
    'css': '🎨',
    'json': '📋',
    'md': '📝'
  };
  return iconMap[ext] || '📄';
};

// Mobile Bottom Nav
const MobileNav = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'chat', icon: MessageSquare, label: 'Chat' },
    { id: 'ide', icon: Code2, label: 'IDE' },
    { id: 'video', icon: Video, label: 'Video' },
    { id: 'image', icon: ImageIcon, label: 'Image' },
    { id: 'clone', icon: Globe, label: 'Clone' },
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
        >
          <tab.icon className="w-5 h-5" strokeWidth={1.5} />
          <span className="text-[10px] font-medium">{tab.label}</span>
        </button>
      ))}
    </div>
  );
};

// Desktop Sidebar
const Sidebar = ({ activeTab, setActiveTab }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const tabs = [
    { id: 'chat', icon: MessageSquare, label: 'AI Chat' },
    { id: 'ide', icon: Code2, label: 'IDE' },
    { id: 'video', icon: Video, label: 'Video' },
    { id: 'image', icon: ImageIcon, label: 'Image' },
    { id: 'clone', icon: Globe, label: 'Clone' },
    { id: 'history', icon: History, label: 'History' },
  ];

  return (
    <div className="hidden md:flex w-16 bg-card border-r border-white/10 flex-col h-screen">
      <div className="h-16 flex items-center justify-center border-b border-white/10">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
          <Atom className="w-5 h-5 text-white" strokeWidth={2} />
        </div>
      </div>

      <div className="flex-1 py-4 flex flex-col items-center gap-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`sidebar-icon w-11 h-11 flex items-center justify-center rounded-xl ${
              activeTab === tab.id ? 'active' : ''
            }`}
            title={tab.label}
          >
            <tab.icon className="w-5 h-5" strokeWidth={1.5} />
          </button>
        ))}
      </div>

      <div className="py-4 flex flex-col items-center border-t border-white/10">
        <button
          onClick={() => { logout(); navigate('/'); }}
          className="sidebar-icon w-11 h-11 flex items-center justify-center rounded-xl text-muted-foreground hover:text-red-400"
          title="Logout"
        >
          <LogOut className="w-5 h-5" strokeWidth={1.5} />
        </button>
      </div>
    </div>
  );
};

// IDE Panel - The main new feature
const IDEPanel = () => {
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [currentFile, setCurrentFile] = useState(null);
  const [code, setCode] = useState('');
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [isAutoFixing, setIsAutoFixing] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [newFileName, setNewFileName] = useState('');
  const [showNewFile, setShowNewFile] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [showNewProject, setShowNewProject] = useState(false);
  const [autoFixEnabled, setAutoFixEnabled] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (currentFile && currentProject) {
      const file = currentProject.files.find(f => f.name === currentFile);
      if (file) {
        setCode(file.content);
      }
    }
  }, [currentFile, currentProject]);

  const loadProjects = async () => {
    try {
      const data = await getProjects();
      setProjects(data);
      if (data.length > 0 && !currentProject) {
        setCurrentProject(data[0]);
        if (data[0].files.length > 0) {
          setCurrentFile(data[0].files[0].name);
        }
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    try {
      const project = await createProject(newProjectName);
      setProjects([project, ...projects]);
      setCurrentProject(project);
      setCurrentFile(project.files[0]?.name);
      setNewProjectName('');
      setShowNewProject(false);
      toast.success('Project created!');
    } catch (error) {
      toast.error('Failed to create project');
    }
  };

  const handleDeleteProject = async (projectId) => {
    try {
      await deleteProject(projectId);
      setProjects(projects.filter(p => p.id !== projectId));
      if (currentProject?.id === projectId) {
        setCurrentProject(null);
        setCurrentFile(null);
        setCode('');
      }
      toast.success('Project deleted');
    } catch (error) {
      toast.error('Failed to delete project');
    }
  };

  const handleCreateFile = async () => {
    if (!newFileName.trim() || !currentProject) return;
    try {
      await addFileToProject(currentProject.id, newFileName);
      const updated = await getProject(currentProject.id);
      setCurrentProject(updated);
      setCurrentFile(newFileName);
      setNewFileName('');
      setShowNewFile(false);
      toast.success('File created!');
    } catch (error) {
      toast.error('Failed to create file');
    }
  };

  const handleDeleteFile = async (filename) => {
    if (!currentProject) return;
    try {
      await deleteFile(currentProject.id, filename);
      const updated = await getProject(currentProject.id);
      setCurrentProject(updated);
      if (currentFile === filename) {
        setCurrentFile(updated.files[0]?.name || null);
      }
      toast.success('File deleted');
    } catch (error) {
      toast.error('Failed to delete file');
    }
  };

  const handleSaveFile = async () => {
    if (!currentProject || !currentFile) return;
    try {
      await updateFile(currentProject.id, currentFile, code);
      const updated = await getProject(currentProject.id);
      setCurrentProject(updated);
      toast.success('Saved!');
    } catch (error) {
      toast.error('Failed to save');
    }
  };

  const getLanguage = () => {
    if (!currentFile) return 'text';
    const ext = currentFile.split('.').pop().toLowerCase();
    const langMap = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'html': 'html',
      'css': 'css',
      'json': 'json',
      'md': 'markdown'
    };
    return langMap[ext] || 'text';
  };

  const handleRunCode = async () => {
    if (!code.trim()) return;
    setIsRunning(true);
    setOutput('Running...\n');

    try {
      const lang = getLanguage();
      
      if (lang === 'html') {
        setShowPreview(true);
        setOutput('HTML preview opened');
        setIsRunning(false);
        return;
      }

      const result = await executeCode(code, lang);
      
      if (result.success) {
        setOutput(result.output || 'Code executed successfully (no output)');
      } else {
        setOutput(`Error:\n${result.error}`);
        
        // Auto-fix if enabled
        if (autoFixEnabled && result.error) {
          setIsAutoFixing(true);
          setOutput(prev => prev + '\n\n⚡ Auto-fixing...\n');
          
          const fixResult = await autoFixLoop(code, lang);
          
          if (fixResult.success) {
            setCode(fixResult.final_code);
            setOutput(`✅ Auto-fixed after ${fixResult.total_attempts} attempt(s):\n\n${fixResult.output}`);
            toast.success('Code auto-fixed!');
          } else {
            setOutput(prev => prev + `\n❌ Could not auto-fix after ${fixResult.total_attempts} attempts`);
          }
          setIsAutoFixing(false);
        }
      }
    } catch (error) {
      setOutput(`Error: ${error.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleManualAutoFix = async () => {
    if (!code.trim() || !output.includes('Error')) return;
    setIsAutoFixing(true);

    try {
      const lang = getLanguage();
      const errorMatch = output.match(/Error[:\s]*([\s\S]*)/);
      const errorMsg = errorMatch ? errorMatch[1] : output;
      
      const result = await autoFixCode(code, lang, errorMsg);
      
      if (result.success) {
        setCode(result.fixed_code);
        setOutput(`✅ Fixed!\n\n${result.explanation}`);
        toast.success('Code fixed!');
      } else {
        toast.error('Could not fix automatically');
      }
    } catch (error) {
      toast.error('Auto-fix failed');
    } finally {
      setIsAutoFixing(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-14 px-4 flex items-center justify-between border-b border-white/10 shrink-0">
        <div className="flex items-center gap-2">
          <Code2 className="w-5 h-5 text-blue-400" strokeWidth={1.5} />
          <span className="font-semibold">ATOM IDE</span>
          <span className="text-xs text-muted-foreground">Auto-Fix {autoFixEnabled ? 'ON' : 'OFF'}</span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={autoFixEnabled ? "default" : "outline"}
            onClick={() => setAutoFixEnabled(!autoFixEnabled)}
            className={`h-8 text-xs ${autoFixEnabled ? 'bg-blue-500 hover:bg-blue-600' : ''}`}
          >
            <Wand2 className="w-3 h-3 mr-1" />
            Auto-Fix
          </Button>
          <Button size="sm" variant="outline" onClick={() => setShowNewProject(true)} className="h-8 text-xs">
            <Plus className="w-3 h-3 mr-1" />
            Project
          </Button>
        </div>
      </div>

      {/* Main IDE Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* File Tree */}
        <div className="w-48 border-r border-white/10 flex flex-col bg-secondary/20">
          <div className="p-2 border-b border-white/10">
            <Select
              value={currentProject?.id || ''}
              onValueChange={(id) => {
                const proj = projects.find(p => p.id === id);
                setCurrentProject(proj);
                setCurrentFile(proj?.files[0]?.name || null);
              }}
            >
              <SelectTrigger className="h-8 text-xs bg-transparent border-white/10">
                <SelectValue placeholder="Select project" />
              </SelectTrigger>
              <SelectContent>
                {projects.map(p => (
                  <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <ScrollArea className="flex-1">
            <div className="p-2 space-y-1">
              {currentProject?.files.map(file => (
                <div
                  key={file.name}
                  className={`flex items-center justify-between p-2 rounded-lg cursor-pointer group ${
                    currentFile === file.name ? 'bg-blue-500/20 text-blue-400' : 'hover:bg-white/5'
                  }`}
                  onClick={() => setCurrentFile(file.name)}
                >
                  <div className="flex items-center gap-2 text-sm truncate">
                    <span>{getFileIcon(file.name)}</span>
                    <span className="truncate">{file.name}</span>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDeleteFile(file.name); }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
              
              {showNewFile ? (
                <div className="flex gap-1 p-1">
                  <Input
                    value={newFileName}
                    onChange={(e) => setNewFileName(e.target.value)}
                    placeholder="filename.js"
                    className="h-7 text-xs bg-transparent border-white/20"
                    onKeyDown={(e) => e.key === 'Enter' && handleCreateFile()}
                    autoFocus
                  />
                  <Button size="sm" onClick={handleCreateFile} className="h-7 w-7 p-0">
                    <Check className="w-3 h-3" />
                  </Button>
                </div>
              ) : (
                <button
                  onClick={() => setShowNewFile(true)}
                  className="flex items-center gap-2 p-2 text-xs text-muted-foreground hover:text-foreground w-full"
                >
                  <Plus className="w-3 h-3" />
                  New File
                </button>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Editor + Output */}
        <div className="flex-1 flex flex-col">
          {/* Editor */}
          <div className="flex-1 relative">
            {currentFile ? (
              <>
                <div className="absolute top-2 right-2 z-10 flex gap-2">
                  <Button size="sm" onClick={handleSaveFile} className="h-7 text-xs bg-secondary/80">
                    Save
                  </Button>
                  {getLanguage() === 'html' && (
                    <Button size="sm" onClick={() => setShowPreview(!showPreview)} className="h-7 text-xs bg-secondary/80">
                      <Eye className="w-3 h-3 mr-1" />
                      Preview
                    </Button>
                  )}
                </div>
                <Editor
                  height="100%"
                  language={getLanguage()}
                  value={code}
                  onChange={(value) => setCode(value || '')}
                  theme="vs-dark"
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    fontFamily: "'JetBrains Mono', monospace",
                    padding: { top: 16 },
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    automaticLayout: true
                  }}
                />
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <FolderOpen className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>Select or create a file to start coding</p>
                </div>
              </div>
            )}
          </div>

          {/* Output/Console */}
          <div className="h-40 border-t border-white/10 flex flex-col">
            <div className="h-9 px-3 flex items-center justify-between border-b border-white/10 bg-secondary/30 shrink-0">
              <div className="flex items-center gap-2 text-sm">
                <Terminal className="w-4 h-4 text-blue-400" />
                <span>Console</span>
              </div>
              <div className="flex items-center gap-2">
                {output.includes('Error') && (
                  <Button
                    size="sm"
                    onClick={handleManualAutoFix}
                    disabled={isAutoFixing}
                    className="h-6 text-xs bg-purple-500 hover:bg-purple-600"
                  >
                    {isAutoFixing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Wand2 className="w-3 h-3 mr-1" />}
                    Fix Error
                  </Button>
                )}
                <Button
                  size="sm"
                  onClick={handleRunCode}
                  disabled={isRunning || !currentFile}
                  className="h-6 text-xs bg-green-500 hover:bg-green-600"
                >
                  {isRunning ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3 mr-1" />}
                  Run
                </Button>
              </div>
            </div>
            <ScrollArea className="flex-1 p-3">
              <pre className="text-xs font-mono whitespace-pre-wrap">
                {output || 'Output will appear here...'}
              </pre>
            </ScrollArea>
          </div>
        </div>

        {/* Live Preview (for HTML) */}
        {showPreview && getLanguage() === 'html' && (
          <div className="w-1/2 border-l border-white/10 flex flex-col">
            <div className="h-9 px-3 flex items-center justify-between border-b border-white/10 bg-secondary/30">
              <span className="text-sm">Live Preview</span>
              <button onClick={() => setShowPreview(false)} className="text-muted-foreground hover:text-foreground">
                <X className="w-4 h-4" />
              </button>
            </div>
            <iframe
              srcDoc={code}
              className="flex-1 bg-white"
              title="Preview"
              sandbox="allow-scripts"
            />
          </div>
        )}
      </div>

      {/* New Project Modal */}
      {showNewProject && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowNewProject(false)}>
          <div className="bg-card border border-white/10 rounded-xl p-6 w-80" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">New Project</h3>
            <Input
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              placeholder="Project name"
              className="mb-4 bg-secondary/50 border-white/10"
              onKeyDown={(e) => e.key === 'Enter' && handleCreateProject()}
              autoFocus
            />
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setShowNewProject(false)}>Cancel</Button>
              <Button onClick={handleCreateProject} className="btn-gradient">Create</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Chat Panel
const ChatPanel = ({ conversationId, setConversationId, onRefresh }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
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
      const response = await sendChatMessage(userMessage, conversationId);
      setConversationId(response.conversation_id);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.response, 
        timestamp: new Date().toISOString() 
      }]);
      onRefresh();
    } catch (error) {
      toast.error('Failed to send message');
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
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
                <button onClick={() => copyToClipboard(code)} className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-foreground">
                  <Copy className="w-3.5 h-3.5" />
                </button>
              </div>
              <pre className="p-4 overflow-x-auto text-sm font-mono"><code>{code}</code></pre>
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
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${isUser ? 'bg-gradient-to-br from-blue-500 to-purple-600' : 'bg-white/10'}`}>
            {isUser ? <span className="text-xs font-bold text-white">U</span> : <Atom className="w-4 h-4 text-blue-400" strokeWidth={2} />}
          </div>
          <div className="flex-1 min-w-0 overflow-hidden">
            <div className="text-xs text-muted-foreground mb-1">{isUser ? 'You' : 'ATOM AI'}</div>
            <div className={`text-sm leading-relaxed ${!isUser ? 'font-mono' : ''}`}>{renderContent(msg.content)}</div>
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 px-4 flex items-center justify-between border-b border-white/10 shrink-0">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-blue-400" strokeWidth={1.5} />
          <span className="font-semibold">AI Assistant</span>
        </div>
        <Button size="sm" variant="ghost" onClick={() => { setConversationId(null); setMessages([]); }} className="h-8">
          <Plus className="w-4 h-4 mr-1" />New
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="py-4">
          {messages.length === 0 ? (
            <div className="text-center py-16 px-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mx-auto mb-4">
                <Atom className="w-8 h-8 text-blue-400" strokeWidth={1.5} />
              </div>
              <h3 className="text-lg font-semibold mb-2">How can I help?</h3>
              <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                Ask me to write code in any language, debug issues, explain concepts, or build entire projects.
              </p>
            </div>
          ) : messages.map((msg, idx) => renderMessage(msg, idx))}
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

      <div className="p-3 md:p-4 border-t border-white/10 shrink-0 pb-20 md:pb-4">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask anything..."
            className="flex-1 h-11 bg-secondary/50 border-white/10 rounded-lg text-sm"
          />
          <Button onClick={handleSend} disabled={loading || !input.trim()} className="h-11 w-11 btn-gradient rounded-lg">
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </Button>
        </div>
      </div>
    </div>
  );
};

// Video Panel with Upload Support
const VideoPanel = () => {
  const [mode, setMode] = useState('text'); // 'text' or 'upload'
  const [prompt, setPrompt] = useState('');
  const [size, setSize] = useState('1280x720');
  const [duration, setDuration] = useState('4');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadPreview, setUploadPreview] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const isImage = file.type.startsWith('image/');
      const isVideo = file.type.startsWith('video/');
      
      if (!isImage && !isVideo) {
        toast.error('Please upload an image or video file');
        return;
      }
      
      setUploadedFile(file);
      
      // Create preview
      if (isImage) {
        const reader = new FileReader();
        reader.onload = (e) => setUploadPreview({ type: 'image', url: e.target.result });
        reader.readAsDataURL(file);
      } else {
        setUploadPreview({ type: 'video', url: URL.createObjectURL(file) });
      }
    }
  };

  const clearUpload = () => {
    setUploadedFile(null);
    setUploadPreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) { 
      toast.error('Enter a prompt'); 
      return; 
    }
    
    if (mode === 'upload' && !uploadedFile) {
      toast.error('Please upload an image or video first');
      return;
    }

    setLoading(true); 
    setVideoUrl(null); 
    setStatus('processing');

    try {
      let response;
      
      if (mode === 'upload' && uploadedFile) {
        // Generate from uploaded media
        response = await generateVideoFromMedia(prompt, uploadedFile, size, parseInt(duration));
      } else {
        // Text to video
        response = await generateVideo(prompt, size, parseInt(duration));
      }
      
      const interval = setInterval(async () => {
        try {
          const statusRes = await getVideoStatus(response.video_id);
          setStatus(statusRes.status);
          if (statusRes.status === 'completed') {
            clearInterval(interval);
            setVideoUrl(`${BACKEND_URL}${statusRes.video_url}`);
            setLoading(false);
            toast.success('Video ready!');
          } else if (statusRes.status === 'failed') {
            clearInterval(interval);
            setLoading(false);
            toast.error('Generation failed');
          }
        } catch (e) {
          console.error('Status check error:', e);
        }
      }, 5000);
      
      setTimeout(() => clearInterval(interval), 900000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed'); 
      setLoading(false); 
      setStatus(null);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 px-4 flex items-center justify-between border-b border-white/10">
        <div className="flex items-center">
          <Video className="w-5 h-5 text-blue-400 mr-2" />
          <span className="font-semibold">Video Generation</span>
          <span className="ml-2 text-xs text-muted-foreground">(Sora 2)</span>
        </div>
      </div>
      
      <div className="flex-1 p-4 md:p-6 overflow-auto pb-20 md:pb-6">
        <div className="max-w-xl mx-auto space-y-4">
          {/* Mode Toggle */}
          <div className="flex gap-2 p-1 bg-secondary/30 rounded-lg">
            <button
              onClick={() => setMode('text')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                mode === 'text' 
                  ? 'bg-blue-500 text-white' 
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Wand2 className="w-4 h-4" />
              Text to Video
            </button>
            <button
              onClick={() => setMode('upload')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                mode === 'upload' 
                  ? 'bg-blue-500 text-white' 
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Upload className="w-4 h-4" />
              From Photo/Video
            </button>
          </div>

          {/* Upload Section */}
          {mode === 'upload' && (
            <div className="space-y-3">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,video/*"
                onChange={handleFileSelect}
                className="hidden"
              />
              
              {!uploadedFile ? (
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full h-32 border-2 border-dashed border-white/20 rounded-xl flex flex-col items-center justify-center gap-2 hover:border-blue-500/50 hover:bg-blue-500/5 transition-colors group"
                >
                  <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center group-hover:bg-blue-500/20 transition-colors">
                    <Plus className="w-6 h-6 text-blue-400" />
                  </div>
                  <span className="text-sm text-muted-foreground">Click to upload image or video</span>
                  <span className="text-xs text-muted-foreground/60">JPG, PNG, WebP, MP4, MOV</span>
                </button>
              ) : (
                <div className="relative rounded-xl overflow-hidden bg-secondary/30 border border-white/10">
                  {uploadPreview?.type === 'image' ? (
                    <img src={uploadPreview.url} alt="Upload preview" className="w-full h-40 object-cover" />
                  ) : (
                    <video src={uploadPreview?.url} className="w-full h-40 object-cover" />
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                  <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {uploadPreview?.type === 'image' ? (
                        <ImageLucide className="w-4 h-4 text-blue-400" />
                      ) : (
                        <Film className="w-4 h-4 text-purple-400" />
                      )}
                      <span className="text-sm text-white truncate">{uploadedFile.name}</span>
                    </div>
                    <button
                      onClick={clearUpload}
                      className="p-1.5 bg-black/40 rounded-full hover:bg-red-500/80 transition-colors"
                    >
                      <X className="w-4 h-4 text-white" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Prompt */}
          <Textarea 
            value={prompt} 
            onChange={(e) => setPrompt(e.target.value)} 
            placeholder={mode === 'upload' 
              ? "Describe how to animate/transform your upload..." 
              : "Describe your video..."
            }
            className="h-24 bg-secondary/50 border-white/10 rounded-lg" 
          />
          
          {/* Settings */}
          <div className="grid grid-cols-2 gap-3">
            <Select value={size} onValueChange={setSize}>
              <SelectTrigger className="bg-secondary/50 border-white/10 h-11"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="1280x720">HD (1280x720)</SelectItem>
                <SelectItem value="1792x1024">Wide (1792x1024)</SelectItem>
                <SelectItem value="1024x1792">Portrait (1024x1792)</SelectItem>
                <SelectItem value="1024x1024">Square (1024x1024)</SelectItem>
              </SelectContent>
            </Select>
            <Select value={duration} onValueChange={setDuration}>
              <SelectTrigger className="bg-secondary/50 border-white/10 h-11"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="4">4 seconds</SelectItem>
                <SelectItem value="8">8 seconds</SelectItem>
                <SelectItem value="12">12 seconds</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {/* Generate Button */}
          <Button 
            onClick={handleGenerate} 
            disabled={loading || (mode === 'upload' && !uploadedFile)} 
            className="w-full h-12 btn-gradient font-semibold rounded-lg"
          >
            {loading ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Generating...</>
            ) : (
              <><Play className="w-4 h-4 mr-2" />Generate Video</>
            )}
          </Button>
          
          {/* Status */}
          {status && (
            <div className="p-4 bg-secondary/30 border border-white/10 rounded-xl">
              <div className="flex items-center gap-2">
                <div className={`status-dot ${status}`} />
                <span className="text-sm font-medium capitalize">{status}</span>
              </div>
              {status === 'processing' && (
                <p className="text-xs text-muted-foreground mt-2">
                  This may take 2-10 minutes. You can leave this page and check back later.
                </p>
              )}
            </div>
          )}
          
          {/* Result */}
          {videoUrl && (
            <div className="video-container rounded-xl">
              <video src={videoUrl} controls className="w-full" />
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

// Image Panel
const ImagePanel = () => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [imageData, setImageData] = useState(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) { toast.error('Enter a prompt'); return; }
    setLoading(true); setImageData(null);
    try {
      const response = await generateImage(prompt);
      setImageData(response.image_data);
      toast.success('Image ready!');
    } catch (error) {
      toast.error('Failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 px-4 flex items-center border-b border-white/10">
        <ImageIcon className="w-5 h-5 text-blue-400 mr-2" />
        <span className="font-semibold">Image Generation</span>
      </div>
      <div className="flex-1 p-4 md:p-6 overflow-auto pb-20 md:pb-6">
        <div className="max-w-xl mx-auto space-y-4">
          <Textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Describe your image..." className="h-28 bg-secondary/50 border-white/10 rounded-lg" />
          <Button onClick={handleGenerate} disabled={loading} className="w-full h-12 btn-gradient font-semibold rounded-lg">
            {loading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Generating...</> : <><ImageIcon className="w-4 h-4 mr-2" />Generate</>}
          </Button>
          {imageData && <div className="image-preview rounded-xl"><img src={`data:image/png;base64,${imageData}`} alt="Generated" className="w-full" /></div>}
        </div>
      </div>
    </div>
  );
};

// Clone Panel
const ClonePanel = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleClone = async () => {
    if (!url.trim()) { toast.error('Enter URL'); return; }
    try { new URL(url); } catch { toast.error('Invalid URL'); return; }
    setLoading(true); setResult(null);
    try {
      const response = await cloneSite(url);
      setResult(response);
      toast.success('Cloned!');
    } catch (error) {
      toast.error('Failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 px-4 flex items-center border-b border-white/10">
        <Globe className="w-5 h-5 text-blue-400 mr-2" />
        <span className="font-semibold">Site Cloner</span>
      </div>
      <div className="flex-1 p-4 md:p-6 overflow-auto pb-20 md:pb-6">
        <div className="max-w-3xl mx-auto space-y-4">
          <div className="flex gap-2">
            <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com" className="flex-1 h-11 bg-secondary/50 border-white/10 rounded-lg font-mono text-sm" />
            <Button onClick={handleClone} disabled={loading} className="h-11 px-6 btn-gradient font-semibold rounded-lg">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Clone'}
            </Button>
          </div>
          {result && (
            <div className="space-y-4">
              <div className="flex gap-3">
                <Button variant="outline" size="sm" onClick={() => { navigator.clipboard.writeText(result.code); toast.success('Copied!'); }}><Copy className="w-3 h-3 mr-1" />Copy</Button>
                <a href={`${BACKEND_URL}${result.preview_url}`} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"><ExternalLink className="w-3 h-3" />Preview</a>
              </div>
              <div className="monaco-container h-[400px] rounded-xl">
                <Editor height="100%" defaultLanguage="html" value={result.code} theme="vs-dark" options={{ readOnly: true, minimap: { enabled: false }, fontSize: 13, wordWrap: 'on' }} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// History Panel
const HistoryPanel = ({ conversations, onSelect, onDelete, onRefresh }) => (
  <div className="flex flex-col h-full">
    <div className="h-14 px-4 flex items-center justify-between border-b border-white/10">
      <div className="flex items-center"><History className="w-5 h-5 text-blue-400 mr-2" /><span className="font-semibold">History</span></div>
      <Button size="sm" variant="ghost" onClick={onRefresh} className="h-8 w-8 p-0"><RefreshCw className="w-4 h-4" /></Button>
    </div>
    <ScrollArea className="flex-1 pb-20 md:pb-0">
      <div className="p-4 space-y-2">
        {conversations.length === 0 ? (
          <div className="text-center py-12"><MessageSquare className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" /><p className="text-sm text-muted-foreground">No history</p></div>
        ) : conversations.map((conv) => (
          <div key={conv.id} className="p-3 bg-secondary/30 border border-white/5 hover:border-blue-500/30 rounded-xl group cursor-pointer" onClick={() => onSelect(conv.id)}>
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0"><h4 className="text-sm font-medium truncate">{conv.title}</h4><p className="text-xs text-muted-foreground mt-1">{conv.messages?.length || 0} messages</p></div>
              <button onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }} className="opacity-0 group-hover:opacity-100 p-1 text-muted-foreground hover:text-red-400"><Trash2 className="w-4 h-4" /></button>
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  </div>
);

// Main Workspace
export default function WorkspacePage() {
  const { user, loading: authLoading, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('chat');
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);

  useEffect(() => {
    if (!authLoading && !user) navigate('/login');
  }, [user, authLoading, navigate]);

  useEffect(() => {
    if (user) loadConversations();
  }, [user]);

  const loadConversations = async () => {
    try { setConversations(await getConversations()); } catch (e) { console.error(e); }
  };

  if (authLoading) return <div className="min-h-screen bg-background flex items-center justify-center"><Loader2 className="w-8 h-8 text-blue-400 animate-spin" /></div>;

  return (
    <div className="bg-background min-h-screen md:grid md:grid-cols-[64px_1fr]">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <MobileNav activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <div className="flex-1 h-screen overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div key={activeTab} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }} className="h-full">
            {activeTab === 'chat' && <ChatPanel conversationId={conversationId} setConversationId={setConversationId} onRefresh={loadConversations} />}
            {activeTab === 'ide' && <IDEPanel />}
            {activeTab === 'video' && <VideoPanel />}
            {activeTab === 'image' && <ImagePanel />}
            {activeTab === 'clone' && <ClonePanel />}
            {activeTab === 'history' && <HistoryPanel conversations={conversations} onSelect={(id) => { setConversationId(id); setActiveTab('chat'); }} onDelete={async (id) => { await deleteConversation(id); loadConversations(); if (conversationId === id) setConversationId(null); }} onRefresh={loadConversations} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
