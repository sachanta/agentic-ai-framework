import { useCallback, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  MarkerType,
} from 'react-flow-renderer';
import { Plus, Save } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StepEditor } from './StepEditor';
import { useUpdateWorkflow } from '@/hooks/useWorkflows';
import type { Workflow, WorkflowStep } from '@/types/workflow';

interface WorkflowBuilderProps {
  workflow: Workflow;
}

const nodeTypes = {
  agent: AgentNode,
  tool: ToolNode,
  condition: ConditionNode,
};

function AgentNode({ data }: { data: { label: string } }) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-blue-100 border-2 border-blue-500">
      <div className="font-bold text-blue-700">Agent</div>
      <div className="text-sm">{data.label}</div>
    </div>
  );
}

function ToolNode({ data }: { data: { label: string } }) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-green-100 border-2 border-green-500">
      <div className="font-bold text-green-700">Tool</div>
      <div className="text-sm">{data.label}</div>
    </div>
  );
}

function ConditionNode({ data }: { data: { label: string } }) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-yellow-100 border-2 border-yellow-500">
      <div className="font-bold text-yellow-700">Condition</div>
      <div className="text-sm">{data.label}</div>
    </div>
  );
}

function stepsToNodes(steps: WorkflowStep[]): Node[] {
  return steps.map((step) => ({
    id: step.id,
    type: step.type === 'agent' ? 'agent' : step.type === 'tool' ? 'tool' : 'condition',
    position: step.position,
    data: { label: step.name },
  }));
}

function stepsToEdges(steps: WorkflowStep[]): Edge[] {
  const edges: Edge[] = [];
  steps.forEach((step) => {
    step.nextSteps.forEach((nextId) => {
      edges.push({
        id: `${step.id}-${nextId}`,
        source: step.id,
        target: nextId,
        markerEnd: { type: MarkerType.ArrowClosed },
      });
    });
  });
  return edges;
}

export function WorkflowBuilder({ workflow }: WorkflowBuilderProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(stepsToNodes(workflow.steps));
  const [edges, setEdges, onEdgesChange] = useEdgesState(stepsToEdges(workflow.steps));
  const [selectedStep, setSelectedStep] = useState<WorkflowStep | null>(null);
  const updateMutation = useUpdateWorkflow();

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const step = workflow.steps.find((s) => s.id === node.id);
      if (step) setSelectedStep(step);
    },
    [workflow.steps]
  );

  const handleAddStep = (type: 'agent' | 'tool' | 'condition') => {
    const newId = `step-${Date.now()}`;
    const newNode: Node = {
      id: newId,
      type,
      position: { x: 250, y: nodes.length * 100 },
      data: { label: `New ${type}` },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const handleSave = () => {
    const updatedSteps: WorkflowStep[] = nodes.map((node) => {
      const existingStep = workflow.steps.find((s) => s.id === node.id);
      const outgoingEdges = edges.filter((e) => e.source === node.id);

      return {
        id: node.id,
        name: node.data.label,
        type: node.type as WorkflowStep['type'],
        config: existingStep?.config ?? {},
        position: node.position,
        nextSteps: outgoingEdges.map((e) => e.target),
      };
    });

    updateMutation.mutate({ id: workflow.id, data: { steps: updatedSteps } });
  };

  return (
    <div className="grid grid-cols-4 gap-4 h-[600px]">
      <div className="col-span-3 border rounded-lg overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
        >
          <Controls />
          <Background />
        </ReactFlow>
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Add Step</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => handleAddStep('agent')}
            >
              <Plus className="mr-2 h-4 w-4" />
              Agent Step
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => handleAddStep('tool')}
            >
              <Plus className="mr-2 h-4 w-4" />
              Tool Step
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => handleAddStep('condition')}
            >
              <Plus className="mr-2 h-4 w-4" />
              Condition
            </Button>
          </CardContent>
        </Card>

        {selectedStep && (
          <StepEditor
            step={selectedStep}
            onClose={() => setSelectedStep(null)}
          />
        )}

        <Button onClick={handleSave} className="w-full" disabled={updateMutation.isPending}>
          <Save className="mr-2 h-4 w-4" />
          Save Workflow
        </Button>
      </div>
    </div>
  );
}
