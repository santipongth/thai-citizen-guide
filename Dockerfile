# ── Stage 1: Build React app ──────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package manifests (support npm / pnpm lock files)
COPY package.json package-lock.json* pnpm-lock.yaml* bun.lock* ./

# Install with npm (falls back gracefully when lock file is present)
RUN npm ci --prefer-offline 2>/dev/null || npm install

# Copy source
COPY . .

# API_BASE_URL is intentionally left empty so the browser sends API
# requests to the same origin (nginx handles proxying to the backend).
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build


# ── Stage 2: Serve with nginx ─────────────────────────────────────────────────
FROM nginx
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx/frontend.conf /etc/nginx/conf.d/default.conf
