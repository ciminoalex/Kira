import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware di autenticazione basilare per il frontend.
 * Usa un cookie di sessione dopo login con password.
 */
export function middleware(request: NextRequest) {
  const authCookie = request.cookies.get("kira-auth");
  const password = process.env.FRONTEND_AUTH_PASSWORD;

  // Se non c'è password configurata, accesso libero
  if (!password) {
    return NextResponse.next();
  }

  // API token è sempre accessibile (protetta da LiveKit)
  if (request.nextUrl.pathname.startsWith("/api/")) {
    return NextResponse.next();
  }

  // Pagina login sempre accessibile
  if (request.nextUrl.pathname === "/login") {
    return NextResponse.next();
  }

  // POST login: verifica password e setta cookie
  if (request.nextUrl.pathname === "/auth" && request.method === "POST") {
    return NextResponse.next();
  }

  // Verifica cookie auth
  if (authCookie?.value === "authenticated") {
    return NextResponse.next();
  }

  // Redirect a login
  return NextResponse.redirect(new URL("/login", request.url));
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
