import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { weaviateApi, type WeaviateProperty } from '@/api/weaviate';
import { notify } from '@/store/notificationStore';

interface CollectionFormProps {
  onSuccess?: () => void;
}

const VECTORIZERS = ['text2vec-openai', 'text2vec-cohere', 'text2vec-huggingface', 'none'];
const DATA_TYPES = ['text', 'string', 'int', 'number', 'boolean', 'date', 'text[]', 'string[]'];

export function CollectionForm({ onSuccess }: CollectionFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [vectorizer, setVectorizer] = useState('text2vec-openai');
  const [properties, setProperties] = useState<WeaviateProperty[]>([]);
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: weaviateApi.createCollection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weaviate', 'collections'] });
      notify.success('Collection created');
      onSuccess?.();
    },
    onError: (error: Error) => {
      notify.error('Failed to create collection', error.message);
    },
  });

  const addProperty = () => {
    setProperties([
      ...properties,
      { name: '', dataType: ['text'], description: '' },
    ]);
  };

  const removeProperty = (index: number) => {
    setProperties(properties.filter((_, i) => i !== index));
  };

  const updateProperty = (index: number, updates: Partial<WeaviateProperty>) => {
    setProperties(
      properties.map((prop, i) => (i === index ? { ...prop, ...updates } : prop))
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      name,
      description,
      vectorizer,
      properties,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Collection Name</Label>
        <Input
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="MyCollection"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Input
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Optional description"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="vectorizer">Vectorizer</Label>
        <Select value={vectorizer} onValueChange={setVectorizer}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {VECTORIZERS.map((v) => (
              <SelectItem key={v} value={v}>
                {v}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label>Properties</Label>
          <Button type="button" variant="outline" size="sm" onClick={addProperty}>
            <Plus className="mr-2 h-4 w-4" />
            Add Property
          </Button>
        </div>

        <div className="space-y-2">
          {properties.map((prop, index) => (
            <div key={index} className="flex gap-2 items-start">
              <Input
                placeholder="Property name"
                value={prop.name}
                onChange={(e) => updateProperty(index, { name: e.target.value })}
              />
              <Select
                value={prop.dataType[0]}
                onValueChange={(value) => updateProperty(index, { dataType: [value] })}
              >
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DATA_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => removeProperty(index)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </div>

      <Button type="submit" className="w-full" disabled={createMutation.isPending}>
        {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        Create Collection
      </Button>
    </form>
  );
}
