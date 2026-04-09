import 'dotenv/config';

export const config = {
  port: parseInt(process.env.PORT || '4000', 10),
  host: process.env.HOST || '0.0.0.0',
  nodeEnv: process.env.NODE_ENV || 'development',
  logLevel: process.env.LOG_LEVEL || 'info',

  // Database
  databaseUrl: process.env.DATABASE_URL || 'postgresql://zroky:zroky_dev_password@localhost:5432/zroky',

  // Redis
  redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',

  // Pub/Sub
  gcpProjectId: process.env.GCP_PROJECT_ID || 'zroky-dev',
  pubsubEmulatorHost: process.env.PUBSUB_EMULATOR_HOST,

  // API Key HMAC secret
  apiKeyHmacSecret: process.env.API_KEY_HMAC_SECRET || 'zroky-dev-hmac-secret',

  // Clerk (dashboard auth — future)
  clerkSecretKey: process.env.CLERK_SECRET_KEY || '',
} as const;
