# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency files first for better caching
COPY package.json package-lock.json* ./
RUN npm install

# Copy the rest of the application source
COPY . .

# Build the Next.js app
RUN npm run build

# Stage 2: Production runtime
FROM node:20-alpine

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /app/package.json ./
COPY --from=builder /app/package-lock.json* ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Set environment variables (optional)
ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

CMD ["npm", "run", "start"]