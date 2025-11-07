/**
 * Hook for detecting mobile/desktop viewport
 */
import { useState, useEffect } from 'react';

const MOBILE_BREAKPOINT = 1024; // lg breakpoint in Tailwind

export function useMobileDetection() {
  const [isMobile, setIsMobile] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Mark as mounted
    setMounted(true);

    const checkMobile = () => {
      const mobile = window.innerWidth < MOBILE_BREAKPOINT;
      setIsMobile(mobile);
    };

    // Initial check
    checkMobile();

    // Listen for resize events
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  return {
    isMobile,
    isDesktop: !isMobile,
    mounted,
  };
}

