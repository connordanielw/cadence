/** Catch-all proxy from /api/proxy/* to BACKEND_URL/*.
 *  Lets the browser only ever talk to its own origin — no CORS surprises in prod.
 */
import { NextRequest, NextResponse } from "next/server";

export const config = {
  api: {
    bodyParser: false,
    responseLimit: false,
  },
};

// Increase body size limit to 50MB for audio/PDF uploads
export const maxDuration = 60;


const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

async function forward(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  const tail = path.join("/");
  const url = new URL(`${BACKEND}/${tail}`);
  req.nextUrl.searchParams.forEach((v, k) => url.searchParams.set(k, v));

  const init: RequestInit = {
    method: req.method,
    headers: stripHopHeaders(req.headers),
    redirect: "manual",
  };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = req.body;
    // @ts-expect-error — needed when streaming a body
    init.duplex = "half";
  }

  let upstream: Response;
  try {
    upstream = await fetch(url, init);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`[proxy] fetch failed → ${url}:`, msg);
    return new NextResponse(JSON.stringify({ error: "proxy_fetch_failed", detail: msg }), {
      status: 502,
      headers: { "content-type": "application/json" },
    });
  }
  // Buffer the body — streaming ReadableStream through NextResponse is unreliable on Vercel.
  const body = await upstream.arrayBuffer();
  return new NextResponse(body, {
    status: upstream.status,
    headers: stripResponseHeaders(upstream.headers),
  });
}

/** Headers that must be stripped from upstream requests. */
function stripHopHeaders(h: Headers): Headers {
  const out = new Headers(h);
  ["host", "connection", "content-length"].forEach((k) => out.delete(k));
  return out;
}

/** Headers that must be stripped from upstream responses.
 *  Node fetch auto-decompresses, so content-encoding/transfer-encoding
 *  from the upstream would mismatch the already-decoded body. */
function stripResponseHeaders(h: Headers): Headers {
  const out = new Headers(h);
  ["content-encoding", "transfer-encoding", "connection", "keep-alive"].forEach((k) => out.delete(k));
  return out;
}

export const GET = forward;
export const POST = forward;
export const PUT = forward;
export const PATCH = forward;
export const DELETE = forward;
