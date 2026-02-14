/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    console.log("Rewrites called (JS). BACKEND_URL:", process.env.BACKEND_URL);
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    console.log("Proxying /api/v1 to:", backendUrl);
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
