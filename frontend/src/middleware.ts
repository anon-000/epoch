import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith('/api/v1')) {
    // Note: In standalone mode, process.env might be inlined at build time if not careful.
    // However, for middleware in Node.js runtime, it should access the process environment.
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    // Clean up URL construction
    const targetBase = backendUrl.replace(/\/$/, '');
    const path = request.nextUrl.pathname;
    const search = request.nextUrl.search;
    
    const finalUrl = `${targetBase}${path}${search}`;
    
    // console.log(`[Middleware] Proxying ${request.url} to ${finalUrl}`);
    return NextResponse.rewrite(new URL(finalUrl));
  }
}

export const config = {
  matcher: '/api/v1/:path*',
}
