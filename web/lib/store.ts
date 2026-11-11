'use client'; import {create} from 'zustand';
type Mode='official'|'demo'|'sandbox'; type State={mode:Mode;setMode:(m:Mode)=>void};
export const useApp=create<State>(set=>({mode:'official',setMode:mode=>set({mode})}));
