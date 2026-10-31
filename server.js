import http from 'node:http';
import app from './src/app.js';
import repo from './src/repositories/csvExpenseRepository.js';
import { PORT } from './src/config.js';

async function bootstrap() {
  try {
    // Auto-create data directory and expenses.csv if missing
    await repo.initialize();
    console.log('[Server] CSV Persistence repository initialized.');

    const server = http.createServer(app);

    server.listen(PORT, () => {
      console.log(`[Server] Smart Expense Tracker running at http://localhost:${PORT}`);
    });

    const shutdown = () => {
      console.log('\n[Server] Gracefully shutting down...');
      server.close(() => {
        console.log('[Server] Closed.');
        process.exit(0);
      });
    };

    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
  } catch (err) {
    console.error('[Server] Fatal startup error:', err);
    process.exit(1);
  }
}

bootstrap();

