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

// Security + ergonomics
app.use(helmet());
app.use(
  cors({
    origin: env.CORS_ORIGIN.split(",").map((o) => o.trim()),
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

app.listen(env.API_GATEWAY_PORT, () => {
  logger.info(
    `🚀 API Gateway running on http://localhost:${env.API_GATEWAY_PORT} (${env.NODE_ENV})`,
  );
});
