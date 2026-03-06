import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Button } from '../components/ui/button';
import { 
  Code2, 
  Video, 
  ImageIcon, 
  Globe, 
  Sparkles, 
  ArrowRight,
  Terminal,
  Layers,
  Atom,
  MessageSquare,
  Palette,
  Zap
} from 'lucide-react';

const FeatureCard = ({ icon: Icon, title, description, delay }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay }}
    className="feature-card p-6 md:p-8 rounded-xl"
  >
    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mb-4">
      <Icon className="w-6 h-6 text-blue-400" strokeWidth={1.5} />
    </div>
    <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
    <p className="text-muted-foreground text-sm leading-relaxed">{description}</p>
  </motion.div>
);

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Hero Glow */}
      <div className="hero-glow" />
      
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-4 md:px-6 py-4 glass border-b border-white/5">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-2"
          >
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Atom className="w-5 h-5 text-white" strokeWidth={2} />
            </div>
            <span className="text-xl font-bold tracking-tight">ATOM</span>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-2 md:gap-4"
          >
            <Button 
              variant="ghost" 
              onClick={() => navigate('/login')}
              className="text-muted-foreground hover:text-foreground text-sm"
              data-testid="nav-login-btn"
            >
              Sign In
            </Button>
            <Button 
              onClick={() => navigate('/register')}
              className="btn-gradient text-white font-medium text-sm px-4 md:px-6 py-2 rounded-lg"
              data-testid="nav-register-btn"
            >
              Get Started
            </Button>
          </motion.div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-28 md:pt-36 pb-16 md:pb-24 px-4 md:px-6 relative">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="text-center max-w-3xl mx-auto"
          >
            <div className="inline-flex items-center gap-2 mb-6 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span className="text-blue-400 text-sm font-medium">AI-Powered Creation</span>
            </div>
            
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-tight mb-6">
              Create with
              <span className="gradient-text"> Intelligence</span>
            </h1>
            
            <p className="text-base md:text-lg text-muted-foreground max-w-xl mx-auto leading-relaxed mb-8 md:mb-10 px-4">
              Your AI workspace for code, videos, and images. Build faster with GPT-5.2, 
              generate stunning videos with Sora 2, and create visuals with Nano Banana.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center px-4">
              <Button 
                size="lg"
                onClick={() => navigate('/register')}
                className="btn-gradient text-white font-semibold text-base px-8 py-6 rounded-xl group w-full sm:w-auto"
                data-testid="hero-cta-btn"
              >
                Start Creating Free
                <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button 
                size="lg"
                variant="outline"
                onClick={() => navigate('/login')}
                className="border-white/10 hover:border-white/20 hover:bg-white/5 font-medium text-base px-8 py-6 rounded-xl w-full sm:w-auto"
                data-testid="hero-signin-btn"
              >
                Sign In
              </Button>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="grid grid-cols-3 gap-4 md:gap-8 mt-16 md:mt-20 max-w-lg mx-auto px-4"
          >
            {[
              { value: 'GPT-5.2', label: 'Code AI' },
              { value: 'Sora 2', label: 'Video Gen' },
              { value: 'Gemini', label: 'Image Gen' }
            ].map((stat, i) => (
              <div key={i} className="text-center">
                <div className="text-lg md:text-2xl font-bold gradient-text">{stat.value}</div>
                <div className="text-xs md:text-sm text-muted-foreground mt-1">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-16 md:py-24 px-4 md:px-6" data-testid="features-section">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-12 md:mb-16"
          >
            <h2 className="text-2xl md:text-4xl font-bold tracking-tight mb-4">
              Everything you need to create
            </h2>
            <p className="text-muted-foreground max-w-lg mx-auto text-sm md:text-base">
              Powerful AI tools designed to help you build, generate, and ship faster.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            <FeatureCard 
              icon={MessageSquare}
              title="AI Code Assistant"
              description="Chat with AI to write, debug, and optimize code in any language. Get instant help with complex problems."
              delay={0.1}
            />
            <FeatureCard 
              icon={Video}
              title="Video Generation"
              description="Transform text into stunning videos with Sora 2. Create 4-12 second clips in multiple formats."
              delay={0.2}
            />
            <FeatureCard 
              icon={Palette}
              title="Image Creation"
              description="Generate beautiful images from descriptions. Perfect for concept art, mockups, and visuals."
              delay={0.3}
            />
            <FeatureCard 
              icon={Globe}
              title="Website Cloner"
              description="Clone any website instantly. Get clean, responsive HTML/CSS code ready for production."
              delay={0.4}
            />
            <FeatureCard 
              icon={Terminal}
              title="Code Editor"
              description="Built-in Monaco editor with syntax highlighting and intelligent code formatting."
              delay={0.5}
            />
            <FeatureCard 
              icon={Layers}
              title="Project History"
              description="All your conversations and generations are saved. Never lose your work again."
              delay={0.6}
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 md:py-24 px-4 md:px-6 border-t border-white/5">
        <div className="max-w-2xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mx-auto mb-6">
              <Zap className="w-8 h-8 text-white" strokeWidth={1.5} />
            </div>
            <h2 className="text-2xl md:text-4xl font-bold tracking-tight mb-4">
              Ready to build something amazing?
            </h2>
            <p className="text-muted-foreground text-sm md:text-base mb-8 max-w-md mx-auto">
              Join thousands of creators using AI to build the future. 
              Free to start, no credit card required.
            </p>
            <Button 
              size="lg"
              onClick={() => navigate('/register')}
              className="btn-gradient text-white font-semibold text-base px-10 py-6 rounded-xl"
              data-testid="cta-register-btn"
            >
              <Sparkles className="mr-2 w-4 h-4" />
              Create Free Account
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-6 md:py-8 px-4 md:px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Atom className="w-4 h-4 text-white" strokeWidth={2} />
            </div>
            <span className="font-semibold">ATOM</span>
          </div>
          <p className="text-xs md:text-sm text-muted-foreground">
            AI-powered code, video, and image generation
          </p>
        </div>
      </footer>
    </div>
  );
}
