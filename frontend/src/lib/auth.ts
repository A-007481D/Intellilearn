export function isLoggedIn(): boolean {
  return !!localStorage.getItem('access_token');
}

export function logout(): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.location.href = '/login';
}

export function getUser(): { email: string; role: string; max_documents: number; max_storage_bytes: number } | null {
  const raw = localStorage.getItem('user');
  return raw ? JSON.parse(raw) : null;
}
