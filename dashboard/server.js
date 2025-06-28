#!/usr/bin/env node

import { readFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join, extname } from 'path';
import { createServer } from 'http';
import { parse } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const mimeTypes = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.gif': 'image/gif',
    '.ico': 'image/x-icon',
    '.svg': 'image/svg+xml',
};

const server = createServer((req, res) => {
    const { pathname } = parse(req.url);

    // Servir les fichiers statiques depuis le dossier build
    const clientDir = join(__dirname, '.svelte-kit/output/client');
    let filePath = join(clientDir, pathname === '/' ? 'index.html' : pathname);

    // Si le fichier n'existe pas, servir index.html (SPA fallback)
    if (!existsSync(filePath)) {
        filePath = join(clientDir, 'index.html');
    }

    if (existsSync(filePath)) {
        const ext = extname(filePath);
        const contentType = mimeTypes[ext] || 'text/plain';

        try {
            const content = readFileSync(filePath);
            res.writeHead(200, {
                'Content-Type': contentType,
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            });
            res.end(content);
        } catch (error) {
            res.writeHead(500);
            res.end('Erreur de lecture du fichier');
        }
    } else {
        res.writeHead(404);
        res.end('Fichier non trouvé');
    }
});

const port = process.env.PORT || 3000;
const host = process.env.HOST || '0.0.0.0';

server.listen(port, host, () => {
    console.log(`🚀 Dashboard WakeDock disponible sur:`);
    console.log(`   - Local:   http://localhost:${port}`);
    console.log(`   - Network: http://${host}:${port}`);
    console.log(`\n🔗 API Backend sur http://localhost:8000`);
    console.log(`📚 Documentation API: http://localhost:8000/api/docs`);
    console.log(`\n👤 Compte de test: admin / admin123`);
});
