import React from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { CipaMemberPortal } from './CipaMemberPortal';
import './styles.css';

const mount = document.getElementById('root');
if (!mount) throw new Error('Elemento da aplicação não encontrado');
createRoot(mount).render(
  <React.StrictMode>
    {location.pathname.replace(/\/$/,'')==='/cipa'?<CipaMemberPortal />:<App />}
  </React.StrictMode>
);

