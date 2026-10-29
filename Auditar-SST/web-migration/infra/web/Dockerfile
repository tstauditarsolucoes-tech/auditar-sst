# Build reproduzivel da primeira interface web; nao publica portas no host.
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json tsconfig.json vite.config.ts index.html ./
RUN npm install --no-audit --no-fund
COPY src/ ./src/
RUN npm run test && npm run build

FROM nginx:stable-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/ /usr/share/nginx/html/
EXPOSE 8080
