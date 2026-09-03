# Auditar EPI

Aplicativo web/PWA para registro de entrega de Equipamentos de Proteção Individual.

## MVP v1
- Cadastro de empresas e CNPJ
- Cadastro de colaboradores por empresa
- Cadastro de EPI com CA, modelo, tamanho e ciclo de troca
- Entrega com vários EPIs no mesmo registro
- Assinatura na tela
- Histórico e comprovante imprimível/salvável em PDF
- Backup JSON
- Funcionamento offline após o primeiro carregamento

## Armazenamento atual
Nesta primeira versão os dados ficam em `localStorage` no aparelho. A próxima etapa é integrar Apps Script/Google Drive para sincronização, PDFs automáticos e pastas por empresa.
