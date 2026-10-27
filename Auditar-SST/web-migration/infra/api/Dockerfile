FROM node:24-alpine
RUN apk add --no-cache su-exec
WORKDIR /srv/auditar
COPY package.json ./
RUN npm install --omit=dev --no-audit --no-fund --ignore-scripts
COPY private-entrypoint.sh server.mjs server.bootstrap.mjs hash-password-stdin.mjs private-bootstrap.smoke.ci.mjs ncService.mjs inspectionService.mjs taskService.mjs authService.mjs server.test.mjs ncService.test.mjs inspectionService.test.mjs taskService.test.mjs integration.ci.test.mjs integration.inspections.ci.test.mjs integration.tasks.ci.test.mjs integration.auth.ci.test.mjs ./
RUN npm test
USER node
ENV NODE_ENV=production PORT=3000
EXPOSE 3000
CMD ["node", "server.mjs"]
