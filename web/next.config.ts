import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // small self-contained server for the Cloud Run image
  devIndicators: false, // keep rehearsal screenshots clean
};

export default nextConfig;
