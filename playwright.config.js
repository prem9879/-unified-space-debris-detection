const { defineConfig } = require('@playwright/test');
const fs = require('fs');

const winVenvPython = '.venv\\Scripts\\python.exe';
const linuxVenvPython = '.venv/bin/python';
const pythonCmd = (process.env.USDD_PYTHON && process.env.USDD_PYTHON.trim()) || (process.platform === 'win32'
  ? (fs.existsSync(winVenvPython) ? winVenvPython : 'python')
  : (fs.existsSync(linuxVenvPython) ? linuxVenvPython : 'python3'));

module.exports = defineConfig({
  testDir: './tests/ui',
  timeout: 60000,
  reporter: [['list'], ['html', { outputFolder: 'artifacts/playwright-report', open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:7870',
    headless: true,
  },
  webServer: {
    command: `"${pythonCmd}" -u webapp/flask_app.py`,
    url: 'http://127.0.0.1:7870/',
    timeout: 300000,
    reuseExistingServer: true,
    env: {
      USDD_PORT: '7870',
      USDD_REQUIRE_AUTH: '0'
    }
  },
});
