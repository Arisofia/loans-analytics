FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Create non-root user and set permissions
RUN adduser -S appuser && chown -R appuser /app
USER appuser
CMD ["node", "dist/index.js"]
