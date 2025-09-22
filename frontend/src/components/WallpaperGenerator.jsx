import React, { useState, useRef } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Loader2, Download, Heart, Share2, Sparkles, Shuffle } from 'lucide-react';
import { toast } from 'sonner';
import { examplePrompts, styleDescriptions } from '../utils/examplePrompts';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API = `${API_BASE}/api`;

// Phone mockup components
const PhoneMockup = ({ imageUrl, phoneType = 'iphone', isLoading = false }) => {
  const phoneStyles = {
    iphone: {
      container: 'relative w-64 h-[520px] bg-black rounded-[3rem] p-2 shadow-2xl',
      screen: 'w-full h-full bg-gray-900 rounded-[2.5rem] overflow-hidden relative',
      notch: 'absolute top-2 left-1/2 transform -translate-x-1/2 w-32 h-6 bg-black rounded-full z-10',
      homeIndicator: 'absolute bottom-2 left-1/2 transform -translate-x-1/2 w-32 h-1 bg-white/30 rounded-full'
    },
    android: {
      container: 'relative w-64 h-[520px] bg-gray-800 rounded-[2rem] p-2 shadow-2xl',
      screen: 'w-full h-full bg-gray-900 rounded-[1.5rem] overflow-hidden relative',
      notch: 'absolute top-2 right-4 w-2 h-2 bg-green-400 rounded-full z-10',
      homeIndicator: 'absolute bottom-2 left-1/2 transform -translate-x-1/2 w-8 h-8 border-2 border-white/30 rounded-full'
    },
    samsung: {
      container: 'relative w-64 h-[520px] bg-gradient-to-b from-blue-900 to-purple-900 rounded-[2.5rem] p-2 shadow-2xl',
      screen: 'w-full h-full bg-gray-900 rounded-[2rem] overflow-hidden relative',
      notch: 'absolute top-3 left-1/2 transform -translate-x-1/2 w-24 h-4 bg-black rounded-full z-10',
      homeIndicator: 'absolute bottom-2 left-1/2 transform -translate-x-1/2 w-24 h-1 bg-white/40 rounded-full'
    }
  };

  const style = phoneStyles[phoneType];

  return (
    <div className={style.container}>
      <div className={style.screen}>
        {style.notch && <div className={style.notch}></div>}

        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-12 h-12 animate-spin text-blue-500" />
          </div>
        ) : imageUrl ? (
          <img
            src={imageUrl}
            alt="Generated wallpaper"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <Sparkles className="w-12 h-12 mb-2" />
            <p className="text-sm text-center px-4">Your AI wallpaper will appear here</p>
          </div>
        )}

        {style.homeIndicator && <div className={style.homeIndicator}></div>}
      </div>
    </div>
  );
};

const WallpaperGenerator = () => {
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('modern');
  const [quality, setQuality] = useState('high');
  const [selectedPhone, setSelectedPhone] = useState('iphone');
  const [generatedImage, setGeneratedImage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState([]);

  const styles = [
    { value: 'modern', label: 'Modern', description: styleDescriptions.modern },
    { value: 'abstract', label: 'Abstract', description: styleDescriptions.abstract },
    { value: 'nature', label: 'Nature', description: styleDescriptions.nature },
    { value: 'minimal', label: 'Minimal', description: styleDescriptions.minimal },
    { value: 'artistic', label: 'Artistic', description: styleDescriptions.artistic },
    { value: 'geometric', label: 'Geometric', description: styleDescriptions.geometric },
    { value: 'gradient', label: 'Gradient', description: styleDescriptions.gradient },
    { value: 'neon', label: 'Neon', description: styleDescriptions.neon }
  ];

  const phoneTypes = [
    { value: 'iphone', label: 'iPhone', icon: '📱' },
    { value: 'android', label: 'Android', icon: '🤖' },
    { value: 'samsung', label: 'Samsung', icon: '📲' }
  ];

  const generateWallpaper = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt for your wallpaper');
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/wallpaper/generate`, {
        prompt: prompt.trim(),
        style,
        aspect_ratio: '9:16',
        quality
      });

      if (response.data.success) {
        setGeneratedImage(response.data.wallpaper_url);
        toast.success('Wallpaper generated successfully!');

        // Add to history
        setHistory(prev => [{
          id: Date.now(),
          prompt,
          style,
          imageUrl: response.data.wallpaper_url,
          timestamp: new Date()
        }, ...prev.slice(0, 9)]); // Keep last 10
      } else {
        toast.error(response.data.error || 'Failed to generate wallpaper');
      }
    } catch (error) {
      console.error('Generation error:', error);
      toast.error('Failed to generate wallpaper. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const downloadWallpaper = () => {
    if (!generatedImage) return;

    const link = document.createElement('a');
    link.href = generatedImage;
    link.download = `wallpaper-${Date.now()}.webp`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Wallpaper downloaded!');
  };

  const shareWallpaper = async () => {
    if (!generatedImage) return;

    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Check out this AI-generated wallpaper!',
          url: generatedImage
        });
      } catch (error) {
        // Fallback to clipboard
        navigator.clipboard.writeText(generatedImage);
        toast.success('Image URL copied to clipboard!');
      }
    } else {
      navigator.clipboard.writeText(generatedImage);
      toast.success('Image URL copied to clipboard!');
    }
  };

  const useRandomPrompt = () => {
    const randomPrompt = examplePrompts[Math.floor(Math.random() * examplePrompts.length)];
    setPrompt(randomPrompt.prompt);
    setStyle(randomPrompt.style);
    toast.success('Random prompt selected!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-2">
            AI Wallpaper Generator
          </h1>
          <p className="text-gray-600 text-lg">Create stunning phone wallpapers with AI</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Controls Panel */}
          <div className="lg:col-span-1">
            <Card className="sticky top-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5" />
                  Generate Wallpaper
                </CardTitle>
                <CardDescription>
                  Describe your dream wallpaper and let AI create it
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Prompt Input */}
                <div className="space-y-2">
                  <Label htmlFor="prompt">Describe your wallpaper</Label>
                  <div className="flex gap-2">
                    <Input
                      id="prompt"
                      placeholder="e.g., Sunset over mountains with purple clouds"
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      className="h-12"
                    />
                    <Button
                      onClick={useRandomPrompt}
                      variant="outline"
                      size="icon"
                      className="h-12 w-12 shrink-0"
                      title="Get random prompt"
                    >
                      <Shuffle className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Style Selection */}
                <div className="space-y-2">
                  <Label>Style</Label>
                  <Select value={style} onValueChange={setStyle}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {styles.map((s) => (
                        <SelectItem key={s.value} value={s.value}>
                          <div>
                            <div className="font-medium">{s.label}</div>
                            <div className="text-sm text-gray-500">{s.description}</div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Quality Selection */}
                <div className="space-y-2">
                  <Label>Quality</Label>
                  <Select value={quality} onValueChange={setQuality}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="high">High Quality</SelectItem>
                      <SelectItem value="medium">Medium Quality</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Generate Button */}
                <Button
                  onClick={generateWallpaper}
                  disabled={isLoading || !prompt.trim()}
                  className="w-full h-12 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generate Wallpaper
                    </>
                  )}
                </Button>

                {/* Action Buttons */}
                {generatedImage && (
                  <div className="flex gap-2">
                    <Button
                      onClick={downloadWallpaper}
                      variant="outline"
                      className="flex-1"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download
                    </Button>
                    <Button
                      onClick={shareWallpaper}
                      variant="outline"
                      className="flex-1"
                    >
                      <Share2 className="w-4 h-4 mr-2" />
                      Share
                    </Button>
                  </div>
                )}

                {/* Example Prompts */}
                <div className="space-y-2">
                  <Label>Example Prompts</Label>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {examplePrompts.slice(0, 6).map((example, index) => (
                      <Button
                        key={index}
                        variant="ghost"
                        className="w-full justify-start text-left h-auto p-3"
                        onClick={() => {
                          setPrompt(example.prompt);
                          setStyle(example.style);
                        }}
                      >
                        <div className="flex flex-col items-start">
                          <span className="text-sm font-medium">{example.prompt}</span>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="secondary" className="text-xs">{example.style}</Badge>
                            <span className="text-xs text-gray-500">{example.description}</span>
                          </div>
                        </div>
                      </Button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Preview Panel */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Phone Preview</CardTitle>
                <CardDescription>
                  See how your wallpaper looks on different phone models
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Phone Type Selector */}
                <div className="flex gap-2 mb-6 justify-center">
                  {phoneTypes.map((phone) => (
                    <Button
                      key={phone.value}
                      onClick={() => setSelectedPhone(phone.value)}
                      variant={selectedPhone === phone.value ? 'default' : 'outline'}
                      className="flex items-center gap-2"
                    >
                      <span>{phone.icon}</span>
                      {phone.label}
                    </Button>
                  ))}
                </div>

                {/* Phone Preview */}
                <div className="flex justify-center">
                  <PhoneMockup
                    imageUrl={generatedImage}
                    phoneType={selectedPhone}
                    isLoading={isLoading}
                  />
                </div>

                {/* Current Generation Info */}
                {generatedImage && (
                  <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-semibold mb-2">Current Wallpaper</h4>
                    <p className="text-sm text-gray-600 mb-2">{prompt}</p>
                    <div className="flex gap-2">
                      <Badge variant="secondary">{style}</Badge>
                      <Badge variant="secondary">{quality} quality</Badge>
                      <Badge variant="secondary">9:16 ratio</Badge>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* History */}
            {history.length > 0 && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Recent Generations</CardTitle>
                  <CardDescription>Your recently generated wallpapers</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {history.map((item) => (
                      <div
                        key={item.id}
                        className="relative group cursor-pointer"
                        onClick={() => setGeneratedImage(item.imageUrl)}
                      >
                        <div className="aspect-[9/16] bg-gray-200 rounded-lg overflow-hidden">
                          <img
                            src={item.imageUrl}
                            alt={item.prompt}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                          />
                        </div>
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-end p-2">
                          <div className="text-white text-xs">
                            <p className="font-medium truncate">{item.prompt}</p>
                            <p className="text-gray-300">{item.style}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WallpaperGenerator;