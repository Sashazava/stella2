# Multi-stage build for Vue 3 frontend with Nginx
# Stage 1: builder — Node.js build environment
FROM node:20-alpine AS builder

# Enable corepack and prepare pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# Copy package files first for layer caching
COPY package.json pnpm-lock.yaml ./

# Install dependencies with frozen lockfile for reproducibility
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build the application
RUN pnpm run build

# Stage 2: runtime — Nginx serving static assets
FROM nginx:alpine AS runtime

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Run Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
