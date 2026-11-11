import type {Config} from 'tailwindcss';
export default {content:['./app/**/*.{ts,tsx}','./components/**/*.{ts,tsx}'],theme:{extend:{colors:{ink:'#050713',panel:'#0b1022',violet:'#8b5cf6',cyan:'#43d9ff'},fontFamily:{sans:['var(--font-sans)'],display:['var(--font-display)']},boxShadow:{glow:'0 0 60px rgba(93,80,255,.18)'}}},plugins:[]} satisfies Config;
