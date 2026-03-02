# ─────────────────────────────────────────────────────────────────────────────
# TechMart CTF Challenge
# CVE-2025-55182 (react2shell) — WAF Bypass Edition
# Category: Web Exploitation | Difficulty: Hard
# ─────────────────────────────────────────────────────────────────────────────

# Stage 1: Install dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json ./
RUN npm install --legacy-peer-deps

# Stage 2: Build Next.js app
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: Production runner
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Create non-root user
RUN addgroup --system --gid 1001 ctfgroup && \
    adduser  --system --uid 1001 ctfuser

# Copy standalone build
COPY --from=builder /app/public                      ./public
COPY --from=builder --chown=ctfuser:ctfgroup /app/.next/standalone ./
COPY --from=builder --chown=ctfuser:ctfgroup /app/.next/static    ./.next/static

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget -q -O /dev/null http://localhost:3000/ || exit 1

# FLAG env var injected by whale at runtime; write flag then drop to ctfuser
CMD ["sh", "-c", \
     "echo \"CHC{r34ct_fl1ght_d3s3r_w4f_byp4ss_1s_4rt_${FLAG}}\" > /flag.txt && \
      chmod 644 /flag.txt && \
      exec su ctfuser -s /bin/sh -c 'node server.js'"]
