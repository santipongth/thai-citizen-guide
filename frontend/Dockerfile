from node:24 as base
env PNPM_HOME="/pnpm" \
    PATH="$PNPM_HOME:$PATH"
run corepack enable && corepack prepare pnpm@latest --activate

workdir /app
copy package.json package-lock.json pnpm-lock.yaml pnpm-workspace.yaml ./
run --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile

from base as development
copy . .
expose 8080
cmd ["pnpm", "run", "dev"]

from base as builder
copy . .
run pnpm run build

from nginx as production
copy --from=builder /app/dist /usr/share/nginx/html
copy nginx.conf /etc/nginx/conf.d/default.conf
expose 8080
healthcheck --interval=30s --timeout=10s --start-period=5s --retries=3 \
    cmd curl -f http://localhost:8080/health || exit 1