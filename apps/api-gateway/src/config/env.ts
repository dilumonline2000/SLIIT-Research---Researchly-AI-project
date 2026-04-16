import dotenv from "dotenv";
import { z } from "zod";

dotenv.config();

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
  API_GATEWAY_PORT: z.coerce.number().default(3001),
  CORS_ORIGIN: z.string().default("http://localhost:3000"),
  LOG_LEVEL: z.string().default("info"),

  SUPABASE_URL: z.string().url(),
  SUPABASE_ANON_KEY: z.string().min(1),
  SUPABASE_SERVICE_ROLE_KEY: z.string().min(1),
  SUPABASE_JWT_SECRET: z.string().optional(),

  MODULE1_URL: z.string().url().default("http://localhost:8001"),
  MODULE2_URL: z.string().url().default("http://localhost:8002"),
  MODULE3_URL: z.string().url().default("http://localhost:8003"),
  MODULE4_URL: z.string().url().default("http://localhost:8004"),
  PAPER_CHAT_URL: z.string().url().default("http://localhost:8005"),
});

const parsed = envSchema.safeParse(process.env);

if (!parsed.success) {
  console.error("Invalid environment variables:");
  console.error(parsed.error.format());
  process.exit(1);
}

export const env = parsed.data;
