const { app, BrowserWindow, shell } = require('electron');
const path = require('path');
const fs = require('fs');

function injectCommercialAuth(win) {
  if (!win || win.isDestroyed()) return;

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

          const ensureVisibleLogin = () => {
            const auth = document.getElementById('gestaoAuthOverlay');
            const gate = document.getElementById('gestaoCommercialBootGate');

            if (auth) {
              auth.classList.remove('hidden');
              auth.style.display = 'flex';
              if (gate) gate.remove();
              return true;
            }

            if (window.GestaoEpiAuth && typeof window.GestaoEpiAuth.logout === 'function') {
              window.GestaoEpiAuth.logout(true, '');
            }

            const authAfter = document.getElementById('gestaoAuthOverlay');
            if (authAfter) {
              authAfter.classList.remove('hidden');
              authAfter.style.display = 'flex';
              if (gate) gate.remove();
              return true;
            }

            return false;
          };

          if (!ensureVisibleLogin()) {
            setTimeout(() => {
              if (!ensureVisibleLogin()) {
                const text = document.getElementById('gestaoCommercialBootText');
                if (text) text.textContent = 'Falha ao abrir o login comercial.';
              }
            }, 300);
          }
        } catch (err) {
          const text = document.getElementById('gestaoCommercialBootText');
          if (text) text.textContent = 'Falha ao abrir o login comercial.';
          console.error('Gestão EPI auth bootstrap:', err);
        }
      })();
    `;

    win.webContents.executeJavaScript(bootstrap, true).catch(err => {
      console.error('Gestão EPI execute auth:', err);
      if (!win.isDestroyed()) {
        win.webContents.executeJavaScript(`
          (() => {
            const text = document.getElementById('gestaoCommercialBootText');
            if (text) text.textContent = 'Falha ao executar o login comercial.';
          })();
        `, true).catch(() => {});
      }
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

  // Registra os eventos ANTES de carregar a página. Assim não existe risco de
  // perder o evento dom-ready em computadores mais rápidos.
  win.webContents.on('dom-ready', () => injectCommercialAuth(win));
  win.webContents.on('did-finish-load', () => injectCommercialAuth(win));

  win.loadFile(path.join(__dirname, 'app', 'index.html')).then(() => {
    // Terceira garantia: executa novamente após a promessa do loadFile concluir.
    setTimeout(() => injectCommercialAuth(win), 150);
  }).catch(err => {
    console.error('Gestão EPI loadFile:', err);
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
