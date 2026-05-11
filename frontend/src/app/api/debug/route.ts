import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    backend_url: process.env.BACKEND_URL ?? "(not set — falling back to localhost:8000)",
    node_env: process.env.NODE_ENV,
  });
}
