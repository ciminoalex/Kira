import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const { password } = await request.json();
  const correctPassword = process.env.FRONTEND_AUTH_PASSWORD;

  if (!correctPassword || password === correctPassword) {
    const response = NextResponse.json({ ok: true });
    response.cookies.set("kira-auth", "authenticated", {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 30, // 30 giorni
      path: "/",
    });
    return response;
  }

  return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
}
