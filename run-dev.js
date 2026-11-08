/**
 * ReviewPilot-AI Development Server Runner
 * Automatically detects virtual environment, checks port availability,
 * and launches FastAPI Uvicorn server seamlessly with 'npm run dev'.
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const net = require('net');

const rootDir = __dirname;
const isWin = process.platform === 'win32';
const PORT = 8000;
const HOST = '127.0.0.1';

// 1. Locate the best Python / Uvicorn executable
function getRunnerCommand() {
  const venvUvicornWin = path.join(rootDir, '.venv', 'Scripts', 'uvicorn.exe');
  const venvUvicornPosix = path.join(rootDir, '.venv', 'bin', 'uvicorn');
  const venvPythonWin = path.join(rootDir, '.venv', 'Scripts', 'python.exe');
  const venvPythonPosix = path.join(rootDir, '.venv', 'bin', 'python');

  if (isWin && fs.existsSync(venvUvicornWin)) {
    return { cmd: venvUvicornWin, args: ['backend.main:app', '--reload', '--port', String(PORT), '--host', HOST] };
  }
  if (!isWin && fs.existsSync(venvUvicornPosix)) {
    return { cmd: venvUvicornPosix, args: ['backend.main:app', '--reload', '--port', String(PORT), '--host', HOST] };
  }
  if (isWin && fs.existsSync(venvPythonWin)) {
    return { cmd: venvPythonWin, args: ['-m', 'uvicorn', 'backend.main:app', '--reload', '--port', String(PORT), '--host', HOST] };
  }
  if (!isWin && fs.existsSync(venvPythonPosix)) {
    return { cmd: venvPythonPosix, args: ['-m', 'uvicorn', 'backend.main:app', '--reload', '--port', String(PORT), '--host', HOST] };
  }

  // Fallback to global python
  return { cmd: 'python', args: ['-m', 'uvicorn', 'backend.main:app', '--reload', '--port', String(PORT), '--host', HOST] };
}

// 2. Check if port 8000 is already in use
function checkPortInUse(port, host) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        resolve(true);
      } else {
        resolve(false);
      }
    });
    server.once('listening', () => {
      server.close();
      resolve(false);
    });
    server.listen(port, host);
  });
}

async function start() {
  console.log(`\n\x1b[36m========================================================\x1b[0m`);
  console.log(`\x1b[36m          REVIEWPILOT AI - DEVELOPMENT RUNNER          \x1b[0m`);
  console.log(`\x1b[36m========================================================\x1b[0m\n`);

  const inUse = await checkPortInUse(PORT, HOST);
  if (inUse) {
    console.log(`\x1b[32m✔ ReviewPilot AI is ALREADY RUNNING and live on port ${PORT}!\x1b[0m`);
    console.log(`\x1b[33m➜ Web Interface:\x1b[0m \x1b[1m\x1b[37mhttp://localhost:${PORT}/\x1b[0m`);
    console.log(`\x1b[33m➜ API Health:\x1b[0m    http://localhost:${PORT}/health\n`);
    console.log(`\x1b[90m(If you wish to restart the server, terminate the existing process or close the terminal running port ${PORT})\x1b[0m\n`);
    return;
  }

  const { cmd, args } = getRunnerCommand();
  console.log(`\x1b[34m[Runner]\x1b[0m Launching FastAPI backend server via:`);
  console.log(`         \x1b[90m${cmd} ${args.join(' ')}\x1b[0m\n`);
  console.log(`\x1b[32m➜ Access ReviewPilot at:\x1b[0m \x1b[1m\x1b[37mhttp://localhost:${PORT}/\x1b[0m\n`);

  const child = spawn(cmd, args, { stdio: 'inherit', shell: false });

  child.on('error', (err) => {
    console.error(`\x1b[31m[Error]\x1b[0m Could not start process: ${err.message}`);
    console.log(`\nPlease ensure the Python virtual environment is set up:`);
    console.log(`  Windows: .\\.venv\\Scripts\\Activate.ps1`);
    console.log(`  Run:     pip install -r requirements.txt\n`);
    process.exit(1);
  });

  child.on('exit', (code) => {
    if (code !== 0 && code !== null) {
      console.log(`\x1b[33m[Notice]\x1b[0m Server exited with code ${code}`);
    }
    process.exit(code || 0);
  });
}

start();
