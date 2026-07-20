import "./globals.css";

export const metadata = { title: "Nicer Homes Pricing", description: "Dynamic pricing operations" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}

