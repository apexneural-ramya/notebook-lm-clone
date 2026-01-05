import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Allow the root page to always be accessible
  if (request.nextUrl.pathname === '/') {
    return NextResponse.next();
  }
  
  // Allow other public routes
  const publicRoutes = ['/login', '/signup', '/privacy', '/terms'];
  if (publicRoutes.includes(request.nextUrl.pathname)) {
    return NextResponse.next();
  }
  
  // For all other routes, continue normally
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - icon.svg (icon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|icon.svg).*)',
  ],
}

