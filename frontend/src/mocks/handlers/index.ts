import { authHandlers } from './auth';
import { agentsHandlers } from './agents';
import { toolsHandlers } from './tools';
import { workflowsHandlers } from './workflows';
import { executionsHandlers } from './executions';
import { healthHandlers } from './health';
import { logsHandlers } from './logs';
import { weaviateHandlers } from './weaviate';
import { mongodbHandlers } from './mongodb';
import { settingsHandlers } from './settings';
import { appsHandlers } from './apps';

export const handlers = [
  ...authHandlers,
  ...agentsHandlers,
  ...toolsHandlers,
  ...workflowsHandlers,
  ...executionsHandlers,
  ...healthHandlers,
  ...logsHandlers,
  ...weaviateHandlers,
  ...mongodbHandlers,
  ...settingsHandlers,
  ...appsHandlers,
];
