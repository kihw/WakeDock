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

# Set build-time environment variables for development
ENV PUBLIC_API_URL=http://195.201.199.226
ENV VITE_API_BASE_URL=/api/v1
ENV VITE_WS_BASE_URL=ws://195.201.199.226
ENV PUBLIC_WS_URL=/ws

# Build the application with comprehensive error handling  
RUN echo "Building SvelteKit application..." && \
    echo "Using local development URLs for internal routing" && \
    echo "PUBLIC_API_URL=${PUBLIC_API_URL}" && \
    echo "VITE_API_BASE_URL=${VITE_API_BASE_URL}" && \
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
