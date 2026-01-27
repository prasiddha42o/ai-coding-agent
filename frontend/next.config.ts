import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a self-contained server bundle (server.js + a pruned
  // node_modules) so the Docker runtime image doesn't need the full
  // dependency tree — see docker/frontend.Dockerfile.
  output: "standalone",
};

export default nextConfig;
