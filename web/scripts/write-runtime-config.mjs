import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

const outputPath = process.argv[2] ?? "public/env.json";
const apiUrl = process.env.APP_API_URL || process.env.VITE_API_URL || "/api";

mkdirSync(dirname(outputPath), { recursive: true });
writeFileSync(outputPath, `${JSON.stringify({ API_URL: apiUrl }, null, 2)}\n`);
