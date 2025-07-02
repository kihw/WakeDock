import { json } from '@sveltejs/kit';

/** @type {import('./$types').RequestHandler} */
export async function GET() {
  return json({
    status: 'healthy',
    service: 'wakedock-dashboard',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
  });
}
