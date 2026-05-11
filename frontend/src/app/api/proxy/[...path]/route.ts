/** Catch-all proxy from /api/proxy/* to BACKEND_URL/*.
 *  Lets the browser only ever talk to its own origin — no CORS surprises in prod.
 */
import { NextRequest, NextResponse } from "next/server";

// Note: uploads bypass this proxy entirely (go straight to Railway via NEXT_PUBLIC_BACKEND_URL)
// so the Vercel 4.5 MB body limit doesn't apply here.
export const maxDuration = 60;

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

function err(status: number, detail: string) {
  return new NextResponse(JSON.stringify({ error: detail }), {
    status,
    headers: { "content-type": "application/json" },
  });
}

async function forward(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  try {
    const { path } = await ctx.params;
    const tail = path.join("/");
    const url = new URL(`${BACKEND}/${tail}`);
    req.nextUrl.searchParams.forEach((v, k) => url.searchParams.set(k, v));

    // Build headers — strip hop-by-hop fields
    const headers = new Headers();
    req.headers.forEach((v, k) => {
      if (!["host", "connection", "content-length", "transfer-encoding"].includes(k)) {
        headers.set(k, v);
      }
    });

    // Buffer body for non-GET requests
    let body: ArrayBuffer | undefined;
    if (req.method !== "GET" && req.method !== "HEAD") {
      body = await req.arrayBuffer();
    }

    let upstream: Response;
    try {
      upstream = await fetch(url.toString(), {
        method: req.method,
        headers,
        body: body ?? null,
        redirect: "manual",
      });
    } catch (fetchErr) {
      const msg = fetchErr instanceof Error ? fetchErr.message : String(fetchErr);
      console.error(`[proxy] fetch failed → ${url}:`, msg);
      return err(502, `upstream unreachable: ${msg}`);
    }

    // Strip response hop-by-hop headers
    const resHeaders = new Headers();
    upstream.headers.forEach((v, k) => {
      if (!["content-encoding", "transfer-encoding", "connection", "keep-alive"].includes(k)) {
        resHeaders.set(k, v);
      }
    });

    const resBody = await upstream.arrayBuffer();
    return new NextResponse(resBody, { status: upstream.status, headers: resHeaders });

  } catch (topErr) {
    const msg = topErr instanceof Error ? topErr.message : String(topErr);
    console.error("[proxy] unhandled error:", msg);
    return err(500, `proxy error: ${msg}`);
  }
}

export const GET    = forward;
export const POST   = forward;
export const PUT    = forward;
export const PATCH  = forward;
export const DELETE = forward;
