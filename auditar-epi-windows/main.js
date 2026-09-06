const { app, BrowserWindow, shell, session, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

function safeFileName(name) {
  const clean = String(name || 'Gestao-EPI-atualizacao.exe').replace(/[<>:"/\\|?*\x00-\x1F]/g, '-').trim();
  return clean.toLowerCase().endsWith('.exe') ? clean : `${clean}.exe`;
}

ipcMain.handle('update:download', async (_event, payload = {}) => {
  const url = String(payload.url || '');
  if (!/^https:\/\//i.test(url)) throw new Error('Endereço de atualização inválido.');
  const fileName = safeFileName(payload.fileName);
  const destination = path.join(app.getPath('downloads'), fileName);
  const response = await fetch(url, {
    redirect: 'follow',
    headers: { 'User-Agent': 'Gestao-EPI-Desktop' }
  });
  if (!response.ok) throw new Error(`Falha no download da atualização (${response.status}).`);
  const buffer = Buffer.from(await response.arrayBuffer());
  if (!buffer.length) throw new Error('O arquivo de atualização veio vazio.');
  fs.writeFileSync(destination, buffer);
  const openError = await shell.openPath(destination);
  if (openError) throw new Error(openError);
  return { ok: true, path: destination };
});

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    backgroundColor: '#f4f7f7',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: false
    }
  });

  win.loadFile(path.join(__dirname, 'app', 'index.html'));

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });

  win.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith('file://')) event.preventDefault();
  });
}

app.whenReady().then(() => {
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    callback(permission === 'media');
  });
  session.defaultSession.setPermissionCheckHandler((webContents, permission) => permission === 'media');

  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
