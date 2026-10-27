import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

// Sonda de homologacao: sem login, dados ou acesso a banco/Apps Script.
export function createApp() {
  return createServer((req, res) => {
    const pathname = new URL(req.url || '/', 'http://localhost').pathname;
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    if (req.method === 'GET' && pathname === '/api/v1/health') {
      res.writeHead(200);
      res.end(JSON.stringify({
        ok: true,
        service: 'auditar-sst-web',
        environment: 'homologacao-isolada',
        productionDataConnected: false
      }));
      return;
    }
    res.writeHead(404);
    res.end(JSON.stringify({ ok: false, code: 'NOT_IMPLEMENTED' }));
  });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT || 3000);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error('PORT invalida');
  }
  createApp().listen(port, '0.0.0.0');
}
