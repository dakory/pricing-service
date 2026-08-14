FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json ./
RUN npm install

FROM node:22-alpine AS builder
WORKDIR /app
ARG BUILD_SHA=dev
ENV NEXT_PUBLIC_BUILD_SHA=${BUILD_SHA}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ARG BUILD_SHA=dev
ENV BUILD_SHA=${BUILD_SHA}
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
