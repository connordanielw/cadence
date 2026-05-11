/** Client-side helpers that hit our own Next.js proxy route. The proxy forwards
 *  to the FastAPI backend, so the browser never needs to know the backend URL. */

export type SourceType = "pdf" | "audio";

export interface PieceTags {
  mood?: string[];
  key?: string | null;
  tempo_feel?: string | null;
  era?: string | null;
  instrumentation?: string[];
  summary?: string | null;
}

export interface Piece {
  id: number;
  title: string;
  source_type: SourceType;
  status: string;
  llm_tags?: PieceTags | null;
  description?: string | null;
  error?: string | null;
  created_at: string;
}

export interface PieceWithScore extends Piece {
  score: number;
}

const ROOT = "/api/proxy";
// Uploads bypass the Vercel proxy (4.5 MB serverless limit) and go straight to Railway.
const UPLOAD_ROOT = process.env.NEXT_PUBLIC_BACKEND_URL
  ? `${process.env.NEXT_PUBLIC_BACKEND_URL}`
  : ROOT;

export async function listLibrary(): Promise<Piece[]> {
  const r = await fetch(`${ROOT}/library`, { cache: "no-store" });
  if (!r.ok) throw new Error(`Library fetch failed: ${r.status}`);
  return r.json();
}

export async function getPiece(id: number): Promise<Piece> {
  const r = await fetch(`${ROOT}/library/${id}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`Piece fetch failed: ${r.status}`);
  return r.json();
}

export async function deletePiece(id: number): Promise<void> {
  const r = await fetch(`${ROOT}/library/${id}`, { method: "DELETE" });
  if (!r.ok && r.status !== 204) throw new Error(`Delete failed: ${r.status}`);
}

export interface SearchFilters {
  mood?: string;
  key?: string;
  era?: string;
  limit?: number;
}

export async function search(q: string, filters: SearchFilters = {}): Promise<PieceWithScore[]> {
  const r = await fetch(`${ROOT}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ q, limit: filters.limit ?? 20, ...filters }),
  });
  if (!r.ok) throw new Error(`Search failed: ${r.status}`);
  return r.json();
}

export async function upload(file: File): Promise<Piece> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${UPLOAD_ROOT}/upload`, { method: "POST", body: fd });
  if (!r.ok) throw new Error(`Upload failed: ${r.status}`);
  return r.json();
}
