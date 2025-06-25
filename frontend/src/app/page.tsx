import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Building2, Calculator, Cpu, Globe, Layers3, Zap } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Building2 className="h-8 w-8 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">StruMind</h1>
          </div>
          <nav className="hidden md:flex items-center space-x-8">
            <Link href="#features" className="text-gray-600 hover:text-gray-900">Features</Link>
            <Link href="#capabilities" className="text-gray-600 hover:text-gray-900">Capabilities</Link>
            <Link href="#pricing" className="text-gray-600 hover:text-gray-900">Pricing</Link>
          </nav>
          <div className="flex items-center space-x-4">
            <Link href="/auth/login">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link href="/auth/register">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Next-Generation<br />
            <span className="text-blue-600">Structural Engineering</span>
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            StruMind combines ETABS, Tekla Structures, and STAAD.Pro into one unified AI-powered 
            cloud-native platform. Design, analyze, and detail structures with unprecedented efficiency.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth/register">
              <Button size="lg" className="px-8 py-3">
                Start Building
              </Button>
            </Link>
            <Link href="/demo">
              <Button variant="outline" size="lg" className="px-8 py-3">
                Watch Demo
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 bg-white">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Everything You Need in One Platform
            </h3>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Replace multiple expensive software licenses with one comprehensive solution
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card>
              <CardHeader>
                <Calculator className="h-10 w-10 text-blue-600 mb-2" />
                <CardTitle>Advanced Analysis</CardTitle>
                <CardDescription>
                  Linear/nonlinear static, modal, response spectrum, and time history analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• P-Delta second-order effects</li>
                  <li>• Dynamic analysis capabilities</li>
                  <li>• Code-based seismic analysis</li>
                  <li>• Advanced load combinations</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <Layers3 className="h-10 w-10 text-green-600 mb-2" />
                <CardTitle>Intelligent Design</CardTitle>
                <CardDescription>
                  Automated design per international codes with AI optimization
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• IS 456, ACI 318, Eurocode 2</li>
                  <li>• IS 800, AISC 360, Eurocode 3</li>
                  <li>• Composite design</li>
                  <li>• AI-powered optimization</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <Building2 className="h-10 w-10 text-purple-600 mb-2" />
                <CardTitle>BIM Integration</CardTitle>
                <CardDescription>
                  Full 3D BIM workflow with IFC, glTF, and DXF support
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Real-time 3D visualization</li>
                  <li>• IFC 4.x import/export</li>
                  <li>• Automated detailing</li>
                  <li>• Collaboration tools</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <Globe className="h-10 w-10 text-orange-600 mb-2" />
                <CardTitle>Cloud-Native</CardTitle>
                <CardDescription>
                  Scalable cloud computing with real-time collaboration
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Multi-tenant SaaS platform</li>
                  <li>• Real-time collaboration</li>
                  <li>• Automatic backups</li>
                  <li>• Mobile access</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <Cpu className="h-10 w-10 text-red-600 mb-2" />
                <CardTitle>AI-Powered</CardTitle>
                <CardDescription>
                  Machine learning algorithms for design optimization
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Automated load generation</li>
                  <li>• Smart design suggestions</li>
                  <li>• Error detection</li>
                  <li>• Performance optimization</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <Zap className="h-10 w-10 text-yellow-600 mb-2" />
                <CardTitle>Lightning Fast</CardTitle>
                <CardDescription>
                  High-performance computing for large-scale projects
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Parallel processing</li>
                  <li>• Optimized algorithms</li>
                  <li>• Instant results</li>
                  <li>• Scalable architecture</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-blue-600 text-white">
        <div className="container mx-auto text-center">
          <h3 className="text-3xl font-bold mb-4">
            Ready to Transform Your Structural Engineering Workflow?
          </h3>
          <p className="text-xl mb-8 opacity-90">
            Join thousands of engineers already using StruMind
          </p>
          <Link href="/auth/register">
            <Button size="lg" variant="secondary" className="px-8 py-3">
              Start Your Free Trial
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 px-4">
        <div className="container mx-auto">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Building2 className="h-6 w-6" />
                <span className="text-lg font-bold">StruMind</span>
              </div>
              <p className="text-gray-400">
                Next-generation structural engineering platform for the modern engineer.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/features">Features</Link></li>
                <li><Link href="/pricing">Pricing</Link></li>
                <li><Link href="/integrations">Integrations</Link></li>
                <li><Link href="/api">API</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Resources</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/docs">Documentation</Link></li>
                <li><Link href="/tutorials">Tutorials</Link></li>
                <li><Link href="/blog">Blog</Link></li>
                <li><Link href="/support">Support</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/about">About</Link></li>
                <li><Link href="/careers">Careers</Link></li>
                <li><Link href="/contact">Contact</Link></li>
                <li><Link href="/privacy">Privacy</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 StruMind. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
