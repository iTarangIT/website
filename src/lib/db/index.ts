import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
    throw new Error('DATABASE_URL is not set');
}

const globalForDb = globalThis as unknown as {
    pgClient: ReturnType<typeof postgres> | undefined;
    dbHostLogged: boolean | undefined;
};

const queryClient = globalForDb.pgClient ?? postgres(connectionString, {
    ssl: 'require',
    prepare: false,
    // Shared AWS RDS (database-2) is a small instance (~79 max_connections)
    // with NO pooler in front, and the CRM app/worker already pool against it.
    // The website is a second consumer, so keep its footprint small.
    // connect_timeout bounds a stalled/unreachable RDS so the attempt errors
    // fast (~10s) instead of hanging on the default.
    max: 3,
    idle_timeout: 20,
    connect_timeout: 10,
});

if (process.env.NODE_ENV !== 'production') {
    globalForDb.pgClient = queryClient;
    // Surface the target host once per dev-server start — the calc_* tables
    // only exist on the DB where migration E-177/E-178 was applied (database-2).
    if (!globalForDb.dbHostLogged) {
        try {
            const u = new URL(connectionString);
            console.log(`[DB] connected to ${u.hostname}${u.pathname}`);
        } catch {
            console.log('[DB] DATABASE_URL set (unparseable URL)');
        }
        globalForDb.dbHostLogged = true;
    }
}

export const db = drizzle(queryClient, { schema });
