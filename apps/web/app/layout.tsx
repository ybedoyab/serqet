import type { Metadata } from "next";
import { Header } from "@/components/Header";
import "./globals.css";

export const metadata: Metadata = {
  title: "SERQET — Authority and consent benchmark",
  description:
    "Trust the action, not the answer. A synthetic FHIR R4 benchmark for authority drift in healthcare agents.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main id="content">{children}</main>
        <footer className="site-footer">
          <div className="wrap">
            <p>
              Synthetic charts only. SERQET is not a medical device, a HIPAA
              certification, or a clinical decision aid. Reference controls are
              not model results.
            </p>
            <p>
              <a href="https://github.com/ybedoyab/serqet">GitHub</a>
              {" · "}
              <a href="/api/health">Health</a>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
