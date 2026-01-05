import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
    wrapperClassName?: string;
    onReset?: () => void;
    label?: string;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);
    }

    private handleReset = () => {
        this.setState({ hasError: false, error: null });
        this.props.onReset?.();
    };

    public render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className={`p-4 bg-red-50/90 border border-red-200 rounded-lg flex flex-col items-center justify-center text-center gap-2 ${this.props.wrapperClassName || 'h-full w-full'}`}>
                    <AlertTriangle className="w-8 h-8 text-red-500 mb-1" />
                    <h3 className="text-sm font-semibold text-red-800">
                        {this.props.label || 'Something went wrong'}
                    </h3>
                    <p className="text-xs text-red-600 max-w-[200px] line-clamp-2">
                        {this.state.error?.message}
                    </p>
                    <button
                        onClick={this.handleReset}
                        className="mt-2 flex items-center gap-1.5 px-3 py-1.5 bg-white border border-red-200 text-red-700 text-xs rounded-full hover:bg-red-50 transition-colors shadow-sm"
                    >
                        <RefreshCw className="w-3 h-3" />
                        Try Again
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}
