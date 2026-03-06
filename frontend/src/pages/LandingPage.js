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
  Zap, 
  ArrowRight,
  Terminal,
  Layers,
  Wand2
} from 'lucide-react';

const FeatureCard = ({ icon: Icon, title, description, delay }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay }}
    className="feature-card bg-card border border-border/40 p-6 md:p-8 relative overflow-hidden group"
  >
    <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
    <div className="relative z-10">
      <div className="w-12 h-12 bg-primary/10 flex items-center justify-center mb-4">
        <Icon className="w-6 h-6 text-primary" strokeWidth={1.5} />
      </div>
      <h3 className="text-xl font-semibold text-foreground mb-2 font-[Outfit]">{title}</h3>
      <p className="text-muted-foreground text-sm leading-relaxed">{description}</p>
    </div>
  </motion.div>
);

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Hero Glow */}
      <div className="hero-glow" />
      
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4 glass border-b border-border/20">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-2"
          >
            <Zap className="w-8 h-8 text-primary" strokeWidth={1.5} />
            <span className="text-2xl font-bold tracking-tight font-[Outfit]">FORGE</span>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-4"
          >
            <Button 
              variant="ghost" 
              onClick={() => navigate('/login')}
              className="text-muted-foreground hover:text-foreground"
              data-testid="nav-login-btn"
            >
              Sign In
            </Button>
            <Button 
              onClick={() => navigate('/register')}
              className="bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider text-xs px-6 neon-glow-hover btn-press"
              data-testid="nav-register-btn"
            >
              Get Started
            </Button>
          </motion.div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 relative">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="max-w-4xl"
          >
            <div className="flex items-center gap-2 mb-6">
              <span className="px-3 py-1 bg-primary/10 border border-primary/20 text-primary text-xs font-medium uppercase tracking-wider">
                AI-Powered
              </span>
              <span className="text-muted-foreground text-sm">Code • Video • Images</span>
            </div>
            
            <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tighter leading-none mb-6 font-[Outfit]">
              <span className="text-foreground">Build</span>
              <br />
              <span className="text-primary">Everything.</span>
            </h1>
            
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl leading-relaxed mb-10">
              Your all-in-one AI workspace. Generate code with GPT-5.2, create videos with Sora 2, 
              design images with Nano Banana, and clone any website instantly.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button 
                size="lg"
                onClick={() => navigate('/register')}
                className="bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider text-sm px-8 py-6 neon-glow-hover btn-press group"
                data-testid="hero-cta-btn"
              >
                Start Creating
                <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button 
                size="lg"
                variant="outline"
                onClick={() => navigate('/login')}
                className="border-border hover:border-primary/50 font-medium text-sm px-8 py-6"
                data-testid="hero-signin-btn"
              >
                Already have an account?
              </Button>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="grid grid-cols-3 gap-8 mt-20 max-w-2xl"
          >
            {[
              { value: 'GPT-5.2', label: 'Code Generation' },
              { value: 'Sora 2', label: 'Video AI' },
              { value: 'Nano Banana', label: 'Image Gen' }
            ].map((stat, i) => (
              <div key={i} className="text-left">
                <div className="text-2xl md:text-3xl font-bold text-primary font-[Outfit]">{stat.value}</div>
                <div className="text-sm text-muted-foreground mt-1">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-6" data-testid="features-section">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight font-[Outfit] mb-4">
              Powerful AI Tools
            </h2>
            <p className="text-muted-foreground max-w-xl">
              Everything you need to build, create, and ship faster than ever before.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard 
              icon={Code2}
              title="AI Code Assistant"
              description="Write, debug, and optimize code with GPT-5.2. Get intelligent suggestions, explanations, and complete functions in any language."
              delay={0.1}
            />
            <FeatureCard 
              icon={Video}
              title="Text-to-Video"
              description="Transform your ideas into stunning videos with Sora 2. Create up to 12-second clips in multiple formats and resolutions."
              delay={0.2}
            />
            <FeatureCard 
              icon={ImageIcon}
              title="Image Generation"
              description="Generate beautiful images with Nano Banana. From concept art to product mockups, create visuals that captivate."
              delay={0.3}
            />
            <FeatureCard 
              icon={Globe}
              title="Site Cloner"
              description="Clone any website instantly. Enter a URL and get production-ready HTML/CSS code with modern, responsive design."
              delay={0.4}
            />
            <FeatureCard 
              icon={Terminal}
              title="Code Editor"
              description="Built-in Monaco editor with syntax highlighting, intelligent autocomplete, and real-time error detection."
              delay={0.5}
            />
            <FeatureCard 
              icon={Layers}
              title="Project History"
              description="Never lose your work. All conversations, generated media, and code are automatically saved and organized."
              delay={0.6}
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 border-t border-border/20">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <Wand2 className="w-12 h-12 text-primary mx-auto mb-6" strokeWidth={1.5} />
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight font-[Outfit] mb-4">
              Ready to forge something amazing?
            </h2>
            <p className="text-muted-foreground text-lg mb-8 max-w-xl mx-auto">
              Join thousands of creators using AI to build the future. 
              Start for free, no credit card required.
            </p>
            <Button 
              size="lg"
              onClick={() => navigate('/register')}
              className="bg-primary text-primary-foreground hover:bg-primary/90 font-bold uppercase tracking-wider text-sm px-10 py-6 neon-glow-hover btn-press"
              data-testid="cta-register-btn"
            >
              <Sparkles className="mr-2 w-4 h-4" />
              Create Free Account
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-border/20">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-primary" strokeWidth={1.5} />
            <span className="font-semibold font-[Outfit]">FORGE AI</span>
          </div>
          <p className="text-sm text-muted-foreground">
            Powered by GPT-5.2, Sora 2, and Nano Banana
          </p>
        </div>
      </footer>
    </div>
  );
}
