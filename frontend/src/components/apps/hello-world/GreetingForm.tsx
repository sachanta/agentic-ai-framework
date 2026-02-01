/**
 * Greeting form for Hello World app
 */
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, Sparkles } from 'lucide-react';
import type { GreetingStyle } from '@/types/app';

interface GreetingFormProps {
  onSubmit: (name: string, style: GreetingStyle) => void;
  isLoading?: boolean;
}

const styleOptions: { value: GreetingStyle; label: string; description: string }[] = [
  { value: 'friendly', label: 'Friendly', description: 'Warm and casual' },
  { value: 'formal', label: 'Formal', description: 'Professional and polite' },
  { value: 'casual', label: 'Casual', description: 'Very informal and relaxed' },
  { value: 'enthusiastic', label: 'Enthusiastic', description: 'Very excited and energetic' },
];

export function GreetingForm({ onSubmit, isLoading }: GreetingFormProps) {
  const [name, setName] = useState('');
  const [style, setStyle] = useState<GreetingStyle>('friendly');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      onSubmit(name.trim(), style);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          Generate a Greeting
        </CardTitle>
        <CardDescription>
          Enter a name and select a greeting style to generate a personalized greeting
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              placeholder="Enter a name..."
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="style">Greeting Style</Label>
            <Select value={style} onValueChange={(value) => setStyle(value as GreetingStyle)} disabled={isLoading}>
              <SelectTrigger id="style">
                <SelectValue placeholder="Select a style" />
              </SelectTrigger>
              <SelectContent>
                {styleOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <div className="flex flex-col">
                      <span>{option.label}</span>
                      <span className="text-xs text-muted-foreground">{option.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button type="submit" className="w-full" disabled={!name.trim() || isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Generate Greeting
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
