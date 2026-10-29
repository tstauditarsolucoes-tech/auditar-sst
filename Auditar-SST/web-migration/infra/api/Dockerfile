FROM node:24-alpine
RUN apk add --no-cache su-exec
WORKDIR /srv/auditar
COPY package.json ./
RUN npm install --omit=dev --no-audit --no-fund --ignore-scripts
COPY private-entrypoint.sh server.mjs server.bootstrap.mjs hash-password-stdin.mjs private-bootstrap.smoke.ci.mjs ncService.mjs inspectionService.mjs taskService.mjs actionPlanService.mjs trainingService.mjs cipaService.mjs integration.cipa.ci.test.mjs integration.training.ci.test.mjs authService.mjs nativeAuthService.mjs integration.native-auth.ci.test.mjs portalService.mjs evidenceService.mjs reportService.mjs reportTextPagination.mjs reportTextPagination.test.mjs trainingReportService.mjs integration.training-attendance.ci.test.mjs legacyCompatibility.mjs nativeDraftContract.mjs nativeDraftContract.test.mjs server.test.mjs ncService.test.mjs inspectionService.test.mjs taskService.test.mjs integration.action-plans.ci.test.mjs portalService.test.mjs evidenceService.test.mjs reportService.test.mjs legacyCompatibility.test.mjs integration.reports.ci.test.mjs integration.evidence.ci.test.mjs integration.portal.ci.test.mjs integration.ci.test.mjs integration.inspections.ci.test.mjs integration.tasks.ci.test.mjs integration.auth.ci.test.mjs ./
COPY cipaPortalAuth.mjs cipaPortalService.mjs cipaPortalMediaService.mjs cipaPortal.test.mjs integration.cipa-portal.ci.test.mjs ./
RUN npm test
USER node
ENV NODE_ENV=production PORT=3000
EXPOSE 3000
CMD ["node", "server.mjs"]

