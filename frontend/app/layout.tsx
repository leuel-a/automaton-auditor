import type {Metadata} from 'next';
import {Poppins} from "next/font/google";
import './globals.css';

const poppins = Poppins({
    subsets: ['latin'],
    weight: ['400', '500', '600', '700'],
    variable: '--font-poppins',
    display: 'swap',
});

export const metadata: Metadata = {
    title: 'Automaton Audit',
    description: '',
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={`${poppins.variable} font-poppins`}>{children}</body>
        </html>
    );
}
