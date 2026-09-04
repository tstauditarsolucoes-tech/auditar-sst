const { app, BrowserWindow, shell } = require('electron');
const path = require('path');
const fs = require('fs');

function injectCommercialAuth(win) {
  try {
    const authPath = path.join(__dirname, 'app', 'auth-gestao.js');
    const upperPath = path.join(__dirname, 'app', 'login-uppercase-gestao.js');
    const authCode = fs.readFileSync(authPath, 'utf8');
    const upperCode = fs.existsSync(upperPath) ? fs.readFileSync(upperPath, 'utf8') : '';

    const bootstrap = `
      (() => {
        try {
          if (!window.GestaoEpiAuth) {
            ${authCode}
          }
          if (!window.__gestaoUppercaseInjected) {
            window.__gestaoUppercaseInjected = true;
            ${upperCode}
          }
          const gate = document.getElementById('gestaoCommercialBootGate');
          const auth = document.getElementById('gestaoAuthOverlay');
          if (gate && auth) gate.remove();
          if (!auth && window.GestaoEpiAuth) {
            window.GestaoEpiAuth.logout(true, '');
          }
        } catch (err) {
          const text = document.getElementById('gestaoCommercialBootText');
          if (text) text.textContent = 'Falha ao abrir o login. Feche e abra o programa novamente.';
          console.error('Gestão EPI auth bootstrap:', err);
        }
      })();
    `;

    win.webContents.executeJavaScript(bootstrap, true).catch(err => {
      console.error('Gestão EPI execute auth:', err);
    });
  } catch (err) {
    console.error('Gestão EPI read auth:', err);
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    backgroundColor: '#f4f7f7',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: false
    }
  });

  win.loadFile(path.join(__dirname, 'app', 'index.html'));

  win.webContents.on('dom-ready', () => {
    injectCommercialAuth(win);
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });

  win.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith('file://')) event.preventDefault();
  });
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
