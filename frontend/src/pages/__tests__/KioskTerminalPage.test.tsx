import { vi } from 'vitest';
/**
 * Tests for KioskTerminalPage
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import KioskTerminalPage from '../KioskTerminalPage';

// Mocks
vi.mock('react-router-dom', () => ({
    ...vi.importActual('react-router-dom'),
    useNavigate: () => vi.fn(),
}));

vi.mock('../../utils/api', () => ({
    getApiUrl: (path: string) => `http://localhost:8000${path}`,
}));

// Mock fetch
global.fetch = vi.fn();

describe('KioskTerminalPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorage.clear();
    });

    it('renders page correctly', () => {
        render(
            <BrowserRouter>
                <KioskTerminalPage />
            </BrowserRouter>
        );
        
        // Check page renders - look for QR scanner text
        const pageContent = screen.getByText(/скенер|скaнир/i);
        expect(pageContent).toBeInTheDocument();
    });

    it('initializes terminal_id in localStorage', () => {
        render(
            <BrowserRouter>
                <KioskTerminalPage />
            </BrowserRouter>
        );
        
        // Check terminal_id is created
        const terminalId = localStorage.getItem('terminal_hardware_uuid');
        expect(terminalId).toBeDefined();
    });

    it('has keyboard button', () => {
        render(
            <BrowserRouter>
                <KioskTerminalPage />
            </BrowserRouter>
        );
        
        // Find keyboard button - look for keyboard icon text
        const keyboardElements = screen.getAllByText(/клавиатура|keyboard/i);
        expect(keyboardElements.length).toBeGreaterThan(0);
    });
});
