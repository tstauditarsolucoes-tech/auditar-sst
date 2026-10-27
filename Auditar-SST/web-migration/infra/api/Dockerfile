FROM node:24-alpine
WORKDIR /srv/auditar
COPY package.json ./
RUN npm install --omit=dev --no-audit --no-fund --ignore-scripts
COPY server.mjs ncService.mjs server.test.mjs ncService.test.mjs integration.ci.test.mjs ./
RUN npm test
USER node
ENV NODE_ENV=production PORT=3000
EXPOSE 3000
CMD ["node", "server.mjs"]
