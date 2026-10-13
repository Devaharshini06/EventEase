import vue from '@vitejs/plugin-vue';
import { spawn, ChildProcess } from 'child_process';
import fs from 'fs';
import net from 'net';
import path from 'path';
import { defineConfig, Plugin } from 'vite';

let flaskProcess: ChildProcess | null = null;

function isPortListening(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(400);
    socket.once('connect', () => {
      socket.destroy();
      resolve(true);
    });
    socket.once('timeout', () => {
      socket.destroy();
      resolve(false);
    });
    socket.once('error', () => {
      socket.destroy();
      resolve(false);
    });
    socket.connect(port, '127.0.0.1');
  });
}

function flaskBackendLauncher(): Plugin {
  return {
    name: 'flask-backend-launcher',
    configureServer() {
      isPortListening(5000).then((listening) => {
        if (!listening && !flaskProcess) {
          const venvPython = path.resolve(__dirname, '.venv/bin/python');
          const pythonBin = fs.existsSync(venvPython) ? venvPython : 'python3';
          flaskProcess = spawn(pythonBin, [path.resolve(__dirname, 'backend/run.py')], {
            cwd: __dirname,
            stdio: 'inherit',
            env: { ...process.env, FLASK_PORT: '5000' },
          });
          flaskProcess.on('exit', () => {
            flaskProcess = null;
          });
        }
      });
    },
  };
}

export default defineConfig(() => {
  return {
    plugins: [vue(), flaskBackendLauncher()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 3000,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:5000',
          changeOrigin: true,
        },
      },
      hmr: process.env.DISABLE_HMR !== 'true',
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
    },
  };
});

