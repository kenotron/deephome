import React, { useEffect, useState, useMemo } from 'react';
import * as Babel from '@babel/standalone';
import * as Lucide from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import { ErrorBoundary } from './ui/ErrorBoundary';

interface DynamicWidgetProps {
    code: string;
}

export function DynamicWidget({ code }: DynamicWidgetProps) {
    const [Component, setComponent] = useState<React.FC | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!code) return;

        try {
            // 1. Transpile JSX/TSX to JS
            // We use allowReturnOutsideFunction to prevent the error if the agent still uses return
            const transformed = Babel.transform(code, {
                presets: ['react'],
                filename: 'widget.tsx',
                parserOpts: {
                    allowReturnOutsideFunction: true
                }
            }).code;

            if (!transformed) throw new Error('Transpilation failed');

            // 2. Prepare code for Execution
            // Strip imports as we provide them via scope/require shim
            let cleanCode = transformed.replace(/import\s+.*?from\s+['"].*?['"];?/g, '');

            // Convert "export default" to "exports.default ="
            cleanCode = cleanCode.replace(/export\s+default\s+/g, 'exports.default = ');

            const funcBody = `
        const exports = {};
        const module = { exports: exports };
        const require = (mod) => {
            if (mod === 'react') return React;
            if (mod === 'lucide-react') return Lucide;
            if (mod === 'framer-motion') return FramerMotion;
            return {};
        };
        
        ${cleanCode}
        
        return module.exports.default || exports.default || (typeof App !== 'undefined' ? App : null) || (typeof Widget !== 'undefined' ? Widget : null);
      `;

            const createComponent = new Function('React', 'Lucide', 'FramerMotion', 'useState', 'useEffect', 'useMemo', funcBody);

            const Result = createComponent(React, Lucide, { motion, AnimatePresence }, useState, useEffect, useMemo);

            if (Result) {
                setComponent(() => Result);
                setError(null);
            } else {
                throw new Error('No component returned (export default or named App/Widget required)');
            }

        } catch (err: any) {
            console.error("Dynamic Render Error:", err);
            setError(err.message);
        }
    }, [code]);

    if (error) {
        return (
            <div className="h-full w-full bg-red-500/10 border border-red-500/20 p-4 rounded-xl overflow-auto text-red-400 text-xs font-mono">
                <strong>Render Error:</strong>
                <pre className="mt-2 whitespace-pre-wrap opacity-70">{error}</pre>
            </div>
        );
    }

    if (!Component) {
        return <div className="h-full w-full flex items-center justify-center text-white/20 animate-pulse">Compiling...</div>;
    }

    return (
        <div className="h-full w-full relative overflow-hidden widget-boundary">
            <ErrorBoundary
                label="Widget Runtime Error"
                onReset={() => {
                    // Force re-render attempt if needed, or just clear error
                    setError(null);
                }}
            >
                <Component />
            </ErrorBoundary>
        </div>
    );
}
