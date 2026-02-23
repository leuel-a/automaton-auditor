# STAGE 1: Base
ARG NODE_VERSION=20

FROM node:${NODE_VERSION}-alpine AS base

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

# STAGE 2: Dependencies
FROM base AS deps

COPY package.json package-lock.json* ./

RUN npm ci

# STAGE 3: Builder
FROM base AS builder

COPY --from=deps /app/node_modules ./node_modules

COPY . .

# Build the app
RUN npm run build

# STAGE 4: Runner
FROM node:${NODE_VERSION}-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

ENV NEXT_TELEMETRY_DISABLED=1

# If using Next standalone output (recommended)
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
