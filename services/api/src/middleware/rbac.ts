/**
 * RBAC Role Middleware
 *
 * For dashboard routes (Clerk JWT). Not used for API key routes.
 * Roles: owner > admin > engineer > analyst > viewer
 */
import type { FastifyRequest, FastifyReply } from 'fastify';

import { error } from '../lib/envelope';

export type Role = 'owner' | 'admin' | 'engineer' | 'analyst' | 'viewer';

/** Role hierarchy — higher index = more privilege */
const ROLE_HIERARCHY: Role[] = ['viewer', 'analyst', 'engineer', 'admin', 'owner'];

function roleLevel(role: Role): number {
  return ROLE_HIERARCHY.indexOf(role);
}

export interface DashboardUser {
  userId: string;
  clientId: string;
  email: string;
  role: Role;
}

/**
 * Require minimum role level for dashboard endpoints
 * Expects request.dashboardUser to be set by Clerk auth plugin
 */
export function requireRole(minimumRole: Role) {
  return async (request: FastifyRequest, reply: FastifyReply) => {
    const user = (request as FastifyRequest & { dashboardUser?: DashboardUser }).dashboardUser;

    if (!user) {
      return reply.status(401).send(
        error('unauthorized', 'Authentication required', 401),
      );
    }

    if (roleLevel(user.role) < roleLevel(minimumRole)) {
      return reply.status(403).send(
        error(
          'insufficient_role',
          `This action requires ${minimumRole} role or higher. Your role: ${user.role}`,
          403,
        ),
      );
    }
  };
}
