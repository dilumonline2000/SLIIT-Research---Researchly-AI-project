'use client';

import { ReactNode, createContext, useContext, useState } from 'react';

interface TooltipContextType {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  side?: 'top' | 'right' | 'bottom' | 'left';
}

const TooltipContext = createContext<TooltipContextType | undefined>(undefined);

export function TooltipProvider({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

interface TooltipProps {
  children: ReactNode;
  side?: 'top' | 'right' | 'bottom' | 'left';
}

export function Tooltip({ children, side = 'top' }: TooltipProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <TooltipContext.Provider value={{ isOpen, setIsOpen, side }}>
      <div
        className="relative inline-block"
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
      >
        {children}
      </div>
    </TooltipContext.Provider>
  );
}

interface TooltipTriggerProps {
  children: ReactNode;
  asChild?: boolean;
}

export function TooltipTrigger({ children }: TooltipTriggerProps) {
  return <>{children}</>;
}

interface TooltipContentProps {
  children: ReactNode;
  className?: string;
  side?: 'top' | 'right' | 'bottom' | 'left';
}

export function TooltipContent({ children, className = '', side: overrideSide }: TooltipContentProps) {
  const context = useContext(TooltipContext);
  if (!context?.isOpen) return null;

  const side = overrideSide || context.side || 'top';

  const positionClasses = {
    top: 'bottom-full mb-2 left-1/2 -translate-x-1/2',
    right: 'left-full ml-2 top-1/2 -translate-y-1/2',
    bottom: 'top-full mt-2 left-1/2 -translate-x-1/2',
    left: 'right-full mr-2 top-1/2 -translate-y-1/2',
  };

  return (
    <div
      className={`absolute ${positionClasses[side]} bg-gray-800 text-white text-xs rounded px-2 py-1 whitespace-normal z-50 pointer-events-none ${className}`}
    >
      {children}
    </div>
  );
}
