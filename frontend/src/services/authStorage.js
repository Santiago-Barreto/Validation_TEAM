const TOKEN_KEY = "validation_team_google_credential";
const USER_KEY = "validation_team_auth_user";

export function getStoredToken() {
  return sessionStorage.getItem(TOKEN_KEY) || "";
}

export function getStoredUser() {
  try {
    const raw = sessionStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function storeSession(credential, user) {
  sessionStorage.setItem(TOKEN_KEY, credential);
  sessionStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
}

export function authHeaders(extra = {}) {
  const token = getStoredToken();
  const headers = { ...extra };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}
