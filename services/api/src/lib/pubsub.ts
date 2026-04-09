import { PubSub, Topic } from '@google-cloud/pubsub';

import { config } from '../config';

let pubsub: PubSub | null = null;
const topicCache = new Map<string, Topic>();

const ENGINE_TOPICS = [
  'safety-events',
  'grounding-events',
  'consistency-events',
  'system-events',
] as const;

export type EngineTopic = (typeof ENGINE_TOPICS)[number];

function getPubSub(): PubSub {
  if (!pubsub) {
    pubsub = new PubSub({ projectId: config.gcpProjectId });
  }
  return pubsub;
}

function getTopic(name: string): Topic {
  const fullName = `zroky-${config.nodeEnv === 'production' ? 'prod' : 'dev'}-${name}`;
  if (!topicCache.has(fullName)) {
    topicCache.set(fullName, getPubSub().topic(fullName));
  }
  return topicCache.get(fullName)!;
}

/** Publish event to the appropriate engine topic */
export async function publishEvent(
  topicName: EngineTopic,
  data: Record<string, unknown>,
  attributes?: Record<string, string>,
): Promise<string> {
  const topic = getTopic(topicName);
  const messageId = await topic.publishMessage({
    json: data,
    attributes: attributes || {},
  });
  return messageId;
}

/** Publish to all 4 engine topics (for trust score events that touch all engines) */
export async function publishToAllEngines(
  data: Record<string, unknown>,
  attributes?: Record<string, string>,
): Promise<string[]> {
  const results = await Promise.all(
    ENGINE_TOPICS.map((topic) => publishEvent(topic, data, attributes)),
  );
  return results;
}
