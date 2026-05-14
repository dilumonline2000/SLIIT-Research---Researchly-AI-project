import express from "express";
import cors from "cors";
import helmet from "helmet";
import compression from "compression";
import { env } from "./config/env";
import { logger, httpLogger } from "./middleware/logger";
import { globalRateLimiter } from "./middleware/rateLimiter";
import { errorHandler, notFoundHandler } from "./middleware/errorHandler";
import router from "./routes";

const app = express();

// Trust Railway's load balancer so express-rate-limit reads X-Forwarded-For correctly
app.set("trust proxy", 1);

// Security + ergonomics
app.use(helmet());
const allowedOrigins = env.CORS_ORIGIN.split(",").map((o) => o.trim());
app.use(
  cors({
    origin: (origin, cb) => {
      // Allow requests with no origin (curl, Postman, server-to-server)
      if (!origin) return cb(null, true);
      // Exact match
      if (allowedOrigins.includes(origin)) return cb(null, true);
      // Allow any Vercel deployment of this project
      if (/^https:\/\/researchly-ai(-[a-z0-9-]+)?\.vercel\.app$/.test(origin)) return cb(null, true);
      cb(new Error(`CORS: ${origin} not allowed`));
    },
    credentials: true,
  }),
);
app.use(compression());
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));
app.use(httpLogger);
app.use(globalRateLimiter);

// Routes
app.use("/api/v1", router);

// Errors
app.use(notFoundHandler);
app.use(errorHandler);

const port = process.env.PORT ? parseInt(process.env.PORT, 10) : env.API_GATEWAY_PORT;
app.listen(port, () => {
  logger.info(
    `🚀 API Gateway running on http://localhost:${port} (${env.NODE_ENV})`,
  );
});
