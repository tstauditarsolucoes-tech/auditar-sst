const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('GestaoEpiDesktop', {
  downloadUpdate: (url, fileName) => ipcRenderer.invoke('update:download', { url, fileName })
});
