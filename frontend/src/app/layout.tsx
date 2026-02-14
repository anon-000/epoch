import type { Metadata } from "next";
import { Sidebar } from "@/components/layout/Sidebar";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Epoch — Job Scheduler Dashboard",
  description: "Distributed job scheduler monitoring and management",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Sidebar />
        <main className="ml-60 min-h-screen p-8">{children}</main>
      </body>
    </html>
  );
}
