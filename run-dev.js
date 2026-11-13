/**
 * ReviewPilot-AI Development Server Runner
 * Automatically detects virtual environment, checks port availability,
 * and launches FastAPI Uvicorn server seamlessly with 'npm run dev'.
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const net = require('net');
const http = require('http');

const rootDir = __dirname;
const isWin = process.platform === 'win32';
const PORT = 8000;
const HOST = '0.0.0.0';

// 1. Locate the best Python executable
function getPythonExecutable() {
  const venvPythonWin = path.join(rootDir, '.venv', 'Scripts', 'python.exe');
  const venvPythonPosix = path.join(rootDir, '.venv', 'bin', 'python');
  if (isWin && fs.existsSync(venvPythonWin)) return venvPythonWin;
  if (!isWin && fs.existsSync(venvPythonPosix)) return venvPythonPosix;
  return 'python';
}

// 2. Locate the best Python / Uvicorn executable for running dev server
function getRunnerCommand() {
  const venvUvicornWin = path.join(rootDir, '.venv', 'Scripts', 'uvicorn.exe');
  const venvUvicornPosix = path.join(rootDir, '.venv', 'bin', 'uvicorn');
  const py = getPythonExecutable();

  if (isWin && fs.existsSync(venvUvicornWin)) {
    return { cmd: venvUvicornWin, args: ['backend.main:app', '--reload', '--port', String(PORT), '--host', HOST] };
  }
  if (!isWin && fs.existsSync(venvUvicornPosix)) {
    return { cmd: venvUvicornPosix, args: ['backend.main:app', '--reload', '--port', String(PORT), '--host', HOST] };
  }
  return { cmd: py, args: ['-m', 'uvicorn', 'backend.main:app', '--reload', '--port', String(PORT), '--host', HOST] };
}

// 3. HTTP Health check verification
function checkHealth() {
  return new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${PORT}/health`, { timeout: 3500 }, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (res.statusCode === 200 && json.status === 'healthy') {
            console.log(`\x1b[32m✔ ReviewPilot AI backend is HEALTHY on http://localhost:${PORT}/health\x1b[0m`);
            console.log(`  Service: ${json.service} | Status: ${json.status}`);
            resolve(true);
          } else {
            console.log(`\x1b[33m⚠ Backend returned status code ${res.statusCode}: ${data}\x1b[0m`);
            resolve(false);
          }
        } catch {
          console.log(`\x1b[33m⚠ Received non-JSON response from backend: ${data.slice(0, 100)}\x1b[0m`);
          resolve(false);
        }
      });
    });

    req.on('error', (err) => {
      console.log(`\x1b[31m✖ Backend is not reachable on http://${HOST}:${PORT} (${err.message})\x1b[0m`);
      resolve(false);
    });

    req.on('timeout', () => {
      req.destroy();
      console.log(`\x1b[31m✖ Backend healthcheck timed out on http://${HOST}:${PORT}\x1b[0m`);
      resolve(false);
    });
  });
}

// 4. Check if port 8000 is already in use
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
  const cliArgs = process.argv.slice(2);

  // CLI Flag: --check
  if (cliArgs.includes('--check') || cliArgs.includes('-c')) {
    console.log(`\x1b[36m[Healthcheck]\x1b[0m Pinging ReviewPilot AI at http://${HOST}:${PORT}/health ...`);
    const healthy = await checkHealth();
    process.exit(healthy ? 0 : 1);
  }

  // CLI Flag: --test
  if (cliArgs.includes('--test') || cliArgs.includes('-t')) {
    const py = getPythonExecutable();
    console.log(`\x1b[36m[Test Runner]\x1b[0m Running integration tests with ${py} ...`);
    const testProc = spawn(py, ['-m', 'unittest', 'tests.test_auth_and_health'], { stdio: 'inherit' });
    testProc.on('exit', (code) => process.exit(code || 0));
    return;
  }

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

  // Clean shutdown handlers to prevent orphaned background processes on port 8000
  const cleanup = () => {
    if (child && !child.killed) {
      try {
        if (isWin) {
          spawn('taskkill', ['/pid', child.pid.toString(), '/f', '/t']);
        } else {
          child.kill('SIGTERM');
        }
      } catch (_) {}
    }
  };

  process.on('SIGINT', () => {
    cleanup();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    cleanup();
    process.exit(0);
  });

  process.on('exit', cleanup);

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
