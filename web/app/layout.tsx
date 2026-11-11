import type {Metadata} from 'next'; import {Inter,Space_Grotesk} from 'next/font/google'; import './globals.css'; import {Shell} from '@/components/shell';
const inter=Inter({subsets:['latin'],variable:'--font-sans'});
const space=Space_Grotesk({subsets:['latin'],variable:'--font-display'});
export const metadata:Metadata={title:'AtomiQ — Quantum Campaign Intelligence',description:'Hybrid quantum-classical campaign intelligence platform'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body className={`${inter.variable} ${space.variable}`}><Shell>{children}</Shell></body></html>}
