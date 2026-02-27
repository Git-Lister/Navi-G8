const API_URL = 'http://localhost:8000/api/v1';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData extends LoginCredentials {}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export async function register(data: RegisterData): Promise<AuthResponse> {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  // After register, we'll auto-login (see below)
  return res.json(); // actually returns UserResponse, but we'll ignore for auto-login
}

export async function login(data: LoginCredentials): Promise<AuthResponse> {
  const formData = new URLSearchParams();
  formData.append('username', data.username);
  formData.append('password', data.password);

  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function saveToken(token: string) {
  localStorage.setItem('access_token', token);
}

export function getToken(): string | null {
  return localStorage.getItem('access_token');
}

export function logout() {
  localStorage.removeItem('access_token');
}