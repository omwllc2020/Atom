import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Zap, ArrowLeft, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !email || !password) {
      toast.error('Please fill in all fields');
      return;
    }
    if (password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    setLoading(true);
    try {
      await register(email, password, name);
      toast.success('Account created successfully!');
      navigate('/workspace');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left Panel - Form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-8 md:px-16 lg:px-24">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Link 
            to="/" 
            className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-12 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to home
          </Link>

          <div className="flex items-center gap-2 mb-8">
            <Zap className="w-8 h-8 text-primary" strokeWidth={1.5} />
            <span className="text-2xl font-bold tracking-tight font-[Outfit]">FORGE</span>
          </div>

          <h1 className="text-3xl md:text-4xl font-bold tracking-tight font-[Outfit] mb-2">
            Create your account
          </h1>
          <p className="text-muted-foreground mb-8">
            Start building with AI in seconds
          </p>

          <form onSubmit={handleSubmit} className="space-y-6 max-w-sm">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="h-12 bg-input border-border focus:border-primary"
                data-testid="register-name-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-12 bg-input border-border focus:border-primary"
                data-testid="register-email-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-12 bg-input border-border focus:border-primary"
                data-testid="register-password-input"
              />
              <p className="text-xs text-muted-foreground">At least 6 characters</p>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider text-xs neon-glow-hover btn-press"
              data-testid="register-submit-btn"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                'Create Account'
              )}
            </Button>
          </form>

          <p className="mt-8 text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link to="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </motion.div>
      </div>

      {/* Right Panel - Decoration */}
      <div className="hidden lg:flex w-1/2 bg-card border-l border-border items-center justify-center relative overflow-hidden">
        <div className="hero-glow" />
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-center z-10"
        >
          <div className="grid grid-cols-2 gap-4 mb-8">
            {['Code', 'Video', 'Image', 'Clone'].map((item, i) => (
              <motion.div
                key={item}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className="w-24 h-24 bg-primary/5 border border-primary/10 flex items-center justify-center"
              >
                <span className="text-xs font-mono text-primary/80">{item}</span>
              </motion.div>
            ))}
          </div>
          <h2 className="text-2xl font-bold font-[Outfit] mb-2">All-in-One AI</h2>
          <p className="text-muted-foreground max-w-xs">
            Everything you need to create amazing projects
          </p>
        </motion.div>
      </div>
    </div>
  );
}
