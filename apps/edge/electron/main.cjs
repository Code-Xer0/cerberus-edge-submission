const { app, BrowserWindow, shell } = require('electron');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const target = process.env.CERBERUS_EDGE_URL || 'http://127.0.0.1:8000/web/cerberus-edge-v3/index.html';
const trusted = new URL(target);
const appPaths = ['/web/cerberus-edge/', '/web/cerberus-edge-v3/'];

function allowed(url) {
  try {
    const next = new URL(url);
    return next.origin === trusted.origin && (
      appPaths.some(prefix => next.pathname.startsWith(prefix)) ||
      next.pathname === '/login' ||
      next.pathname === '/' ||
      next.pathname === '/web/index_modern_legacy.html'
    );
  } catch { return false; }
}

app.whenReady().then(async () => {
  const win = new BrowserWindow({
    width: 1600, height: 980, minWidth: 1050, minHeight: 680,
    backgroundColor: '#080b11', title: 'Cerberus Edge',
    icon: path.join(__dirname, '../dist/assets/cerberus-edge-icon.png'),
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true }
  });
  win.webContents.setWindowOpenHandler(({url}) => {
    if (allowed(url)) shell.openExternal(url);
    return {action: 'deny'};
  });
  win.webContents.on('will-navigate', (event, url) => {
    if (!allowed(url)) event.preventDefault();
  });
  try {
    const response = await fetch(target, { signal: AbortSignal.timeout(4500) });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    await win.loadURL(target);
  } catch {
    await win.loadURL(pathToFileURL(path.join(__dirname, '../dist/index.html')).toString());
  }
});
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
