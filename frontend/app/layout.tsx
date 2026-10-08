import "./globals.css";

export const metadata = {
  title: "TVN Media Copilot",
  description: "Copiloto editorial con evidencia trazable y revisión humana",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="es"><body>{children}</body></html>;
}
