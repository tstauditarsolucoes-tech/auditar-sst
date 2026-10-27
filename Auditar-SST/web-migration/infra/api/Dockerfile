FROM node:24-alpine
WORKDIR /srv/auditar
COPY server.mjs ncService.mjs server.test.mjs ncService.test.mjs ./
RUN node --test server.test.mjs ncService.test.mjs
USER node
ENV NODE_ENV=production PORT=3000
EXPOSE 3000
CMD ["node", "server.mjs"]
