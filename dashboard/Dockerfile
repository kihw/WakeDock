FROM node:18-alpine

WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Copy package files
COPY package*.json ./

# Install dependencies with legacy peer deps to resolve conflicts
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build arguments to pass API URL to the build
ARG WAKEDOCK_API_URL=http://wakedock:8000
ARG VITE_API_BASE_URL=${WAKEDOCK_API_URL}/api/v1

# Set environment variables for build
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV WAKEDOCK_API_URL=${WAKEDOCK_API_URL}
ENV PUBLIC_API_URL=${WAKEDOCK_API_URL}
ENV PUBLIC_WS_URL=${WAKEDOCK_API_URL}/ws

# Build the application with comprehensive error handling
RUN echo "Building SvelteKit application..." && \
    echo "API URL: ${VITE_API_BASE_URL}" && \
    npm run build && \
    echo "Build completed, checking output..." && \
    ls -la build/ && \
    test -f build/index.js || (echo "❌ Build failed: index.js not found in build/" && ls -la build/ && exit 1) && \
    echo "✅ Dashboard build successful"

# Clean up devDependencies after build to reduce image size
RUN npm prune --production

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S svelte -u 1001 -G nodejs

# Change ownership of the app directory
RUN chown -R svelte:nodejs /app
USER svelte

# Expose port
EXPOSE 3000

# Improved health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:3000/health || curl -f http://localhost:3000/ || exit 1

# Start the application with proper signal handling
CMD ["node", "build/index.js"]
