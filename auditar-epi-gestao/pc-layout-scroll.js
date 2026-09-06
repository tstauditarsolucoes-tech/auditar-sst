(() => {
  if (document.getElementById('gestao-pc-independent-scroll')) return;

  const style = document.createElement('style');
  style.id = 'gestao-pc-independent-scroll';
  style.textContent = `
    @media (min-width: 721px) {
      html, body {
        height: 100%;
        overflow: hidden;
      }

      .layout {
        height: 100vh;
        min-height: 0;
        overflow: hidden;
      }

      .sidebar {
        height: 100vh;
        overflow-y: auto;
        overflow-x: hidden;
        overscroll-behavior: contain;
        scrollbar-gutter: stable;
      }

      .main {
        height: 100vh;
        min-height: 0;
        overflow-y: auto;
        overflow-x: hidden;
        overscroll-behavior: contain;
      }

      .sidebar::-webkit-scrollbar {
        width: 7px;
      }

      .sidebar::-webkit-scrollbar-track {
        background: transparent;
      }

      .sidebar::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,.20);
        border-radius: 999px;
      }

      .sidebar::-webkit-scrollbar-thumb:hover {
        background: rgba(255,255,255,.34);
      }
    }
  `;

  document.head.appendChild(style);
})();
