import { API_URL } from "../config/api";

const STORAGE_KEY = "gaia2026_team_comments_queue";

function readQueue() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeQueue(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export function enqueueOfflineComment(payload) {
  const q = readQueue();
  q.push({ payload, createdAt: new Date().toISOString() });
  writeQueue(q);
}

export function getQueuedCount() {
  return readQueue().length;
}

export async function flushOfflineCommentQueue(onProgress) {
  if (typeof navigator !== "undefined" && !navigator.onLine) return 0;

  const q = readQueue();
  if (!q.length) return 0;

  let sent = 0;
  const remaining = [];

  for (const item of q) {
    try {
      const res = await fetch(`${API_URL}/guardar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(item.payload),
      });
      if (res.ok) {
        sent += 1;
        onProgress?.(sent);
      } else {
        remaining.push(item);
      }
    } catch {
      remaining.push(item);
    }
  }

  writeQueue(remaining);
  return sent;
}
