import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Dock } from '../modules/dashboard/components/Dock';

describe('Dock Component', () => {
    it('renders input field', () => {
        render(<Dock />);
        expect(screen.getByPlaceholderText('I want to...')).toBeInTheDocument();
    });

    it('calls onSubmit when Enter is pressed', () => {
        const handleSubmit = vi.fn();
        render(<Dock onSubmit={handleSubmit} />);

        const input = screen.getByPlaceholderText('I want to...');
        fireEvent.change(input, { target: { value: 'Create a clock' } });
        fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

        expect(handleSubmit).toHaveBeenCalledWith('Create a clock');
    });

    it('does not submit empty input', () => {
        const handleSubmit = vi.fn();
        render(<Dock onSubmit={handleSubmit} />);

        const input = screen.getByPlaceholderText('I want to...');
        fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

        expect(handleSubmit).not.toHaveBeenCalled();
    });
});
